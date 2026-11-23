# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import datetime
import importlib
import threading
import types as stdlib_types
import typing
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from . import types

__all__ = (
    "ModelConversionError",
    "ModelDefinitionError",
    "ModelField",
    "ModelValue",
)


YdbType = typing.Union[types.PrimitiveType, types.AbstractTypeBuilder]


class ModelDefinitionError(ValueError):
    """Raised when a Python model cannot be mapped to a YDB type."""


class ModelConversionError(ValueError):
    """Raised when a model value cannot be converted to or from YDB data."""


@dataclass(frozen=True)
class ModelField:
    """Per-field YDB mapping metadata for ``typing.Annotated``."""

    ydb_type: typing.Optional[YdbType] = None
    column_name: typing.Optional[str] = None


@dataclass(frozen=True)
class ModelValue:
    """A value accompanied by a Python annotation used for YDB type inference."""

    value: typing.Any
    annotation: typing.Any


@dataclass(frozen=True)
class _ProviderField:
    name: str
    annotation: typing.Any
    required: bool


class _ModelProvider:
    def fields(self) -> typing.Sequence[_ProviderField]:
        raise NotImplementedError

    def construct(self, values: typing.Mapping[str, typing.Any]) -> typing.Any:
        raise NotImplementedError


def _type_hints(model_type: type) -> typing.Mapping[str, typing.Any]:
    try:
        return typing.get_type_hints(model_type, include_extras=True)
    except (NameError, TypeError):
        return getattr(model_type, "__annotations__", {})


class _DataclassProvider(_ModelProvider):
    def __init__(self, model_type: type) -> None:
        self._model_type = model_type

    def fields(self) -> typing.Sequence[_ProviderField]:
        hints = _type_hints(self._model_type)
        result = []
        for field in dataclasses.fields(self._model_type):
            if not field.init:
                continue
            annotation = hints.get(field.name, field.type)
            required = field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING
            result.append(_ProviderField(field.name, annotation, required))
        return result

    def construct(self, values: typing.Mapping[str, typing.Any]) -> typing.Any:
        return self._model_type(**values)


class _PydanticV2Provider(_ModelProvider):
    def __init__(self, model_type: type) -> None:
        self._model_type: typing.Any = model_type

    def fields(self) -> typing.Sequence[_ProviderField]:
        hints = _type_hints(self._model_type)
        result = []
        for name, field in self._model_type.model_fields.items():
            annotation = hints.get(name, field.annotation)
            result.append(_ProviderField(name, annotation, field.is_required()))
        return result

    def construct(self, values: typing.Mapping[str, typing.Any]) -> typing.Any:
        try:
            return self._model_type.model_validate(values, by_name=True)
        except TypeError:
            return self._model_type.model_validate(values)


class _PydanticV1Provider(_ModelProvider):
    def __init__(self, model_type: type) -> None:
        self._model_type: typing.Any = model_type

    def fields(self) -> typing.Sequence[_ProviderField]:
        hints = _type_hints(self._model_type)
        result = []
        for name, field in self._model_type.__fields__.items():
            annotation = hints.get(name, field.outer_type_)
            result.append(_ProviderField(name, annotation, field.required))
        return result

    def construct(self, values: typing.Mapping[str, typing.Any]) -> typing.Any:
        aliased_values = {}
        for name, field in self._model_type.__fields__.items():
            if name in values:
                aliased_values[field.alias or name] = values[name]
        return self._model_type.parse_obj(aliased_values)


def _pydantic_provider(model_type: type) -> typing.Optional[_ModelProvider]:
    try:
        pydantic = importlib.import_module("pydantic")
    except ImportError:
        return None

    base_model = getattr(pydantic, "BaseModel", None)
    if base_model is not None and issubclass(model_type, base_model):
        if hasattr(model_type, "model_fields") and hasattr(model_type, "model_validate"):
            return _PydanticV2Provider(model_type)
        return _PydanticV1Provider(model_type)

    try:
        pydantic_v1 = importlib.import_module("pydantic.v1")
    except ImportError:
        return None
    base_model_v1 = getattr(pydantic_v1, "BaseModel", None)
    if base_model_v1 is not None and issubclass(model_type, base_model_v1):
        return _PydanticV1Provider(model_type)
    return None


def _model_provider(model_type: typing.Any) -> typing.Optional[_ModelProvider]:
    if not isinstance(model_type, type):
        return None
    if dataclasses.is_dataclass(model_type):
        return _DataclassProvider(model_type)
    return _pydantic_provider(model_type)


_DEFAULT_TYPE_MAPPING: typing.Mapping[type, YdbType] = {
    bool: types.PrimitiveType.Bool,
    int: types.PrimitiveType.Int64,
    float: types.PrimitiveType.Double,
    str: types.PrimitiveType.Utf8,
    bytes: types.PrimitiveType.String,
    datetime.date: types.PrimitiveType.Date,
    datetime.datetime: types.PrimitiveType.Timestamp,
    datetime.timedelta: types.PrimitiveType.Interval,
    uuid.UUID: types.PrimitiveType.UUID,
}


def validate_type_mapping(type_mapping: typing.Optional[typing.Mapping[type, YdbType]]) -> None:
    if type_mapping is None:
        return
    if not isinstance(type_mapping, typing.Mapping):
        raise TypeError("type_mapping must be a mapping from Python types to YDB types")
    for python_type, ydb_type in type_mapping.items():
        if not isinstance(python_type, type):
            raise TypeError("type_mapping keys must be Python types")
        _validate_ydb_type(ydb_type, "type_mapping")


def _validate_ydb_type(ydb_type: typing.Any, source: str) -> None:
    if not isinstance(ydb_type, (types.PrimitiveType, types.AbstractTypeBuilder)):
        raise ModelDefinitionError(f"{source} must contain a YDB type, got {ydb_type!r}")


def _unwrap_annotated(annotation: typing.Any) -> typing.Tuple[typing.Any, typing.Optional[ModelField]]:
    if typing.get_origin(annotation) is not typing.Annotated:
        return annotation, None
    arguments = typing.get_args(annotation)
    model_fields = [metadata for metadata in arguments[1:] if isinstance(metadata, ModelField)]
    if len(model_fields) > 1:
        raise ModelDefinitionError("A model field can contain only one ModelField annotation")
    return arguments[0], model_fields[0] if model_fields else None


def _optional_item(annotation: typing.Any) -> typing.Optional[typing.Any]:
    origin = typing.get_origin(annotation)
    if origin not in (typing.Union, stdlib_types.UnionType):
        return None
    arguments = typing.get_args(annotation)
    non_none = tuple(argument for argument in arguments if argument is not type(None))
    if len(arguments) == 2 and len(non_none) == 1:
        return non_none[0]
    return None


class _ValueAdapter:
    __slots__ = ("annotation", "ydb_type", "kind", "item", "key", "payload", "model")

    def __init__(
        self,
        annotation: typing.Any,
        ydb_type: YdbType,
        kind: str,
        *,
        item: typing.Optional["_ValueAdapter"] = None,
        key: typing.Optional["_ValueAdapter"] = None,
        payload: typing.Optional["_ValueAdapter"] = None,
        model: typing.Optional["_ModelAdapter"] = None,
    ) -> None:
        self.annotation = annotation
        self.ydb_type = ydb_type
        self.kind = kind
        self.item = item
        self.key = key
        self.payload = payload
        self.model = model

    @property
    def nullable(self) -> bool:
        return self.kind == "optional"

    def from_db(self, value: typing.Any, path: str) -> typing.Any:
        if value is None:
            if self.nullable:
                return None
            raise ModelConversionError(f"Column {path!r} is NULL, but the model field is not optional")
        try:
            if self.kind == "optional":
                return typing.cast(_ValueAdapter, self.item).from_db(value, path)
            if self.kind == "list":
                return [typing.cast(_ValueAdapter, self.item).from_db(item, f"{path}[]") for item in value]
            if self.kind == "dict":
                key_adapter = typing.cast(_ValueAdapter, self.key)
                value_adapter = typing.cast(_ValueAdapter, self.payload)
                return {
                    key_adapter.from_db(key, f"{path}.key"): value_adapter.from_db(payload, f"{path}.value")
                    for key, payload in value.items()
                }
            if self.kind == "model":
                return typing.cast(_ModelAdapter, self.model).from_row(value, strict_columns=False, path=path)
            return _coerce_primitive(value, self.annotation, self.ydb_type)
        except ModelConversionError:
            raise
        except Exception as error:
            raise ModelConversionError(f"Failed to convert {path!r} to {self.annotation!r}: {error}") from error


@dataclass(frozen=True)
class _ModelFieldSpec:
    attribute_name: str
    column_name: str
    value_adapter: _ValueAdapter
    required: bool


class _ModelAdapter:
    __slots__ = ("model_type", "provider", "fields", "struct_type", "_fields_by_column")

    def __init__(
        self,
        model_type: type,
        provider: _ModelProvider,
        fields: typing.Sequence[_ModelFieldSpec],
    ) -> None:
        self.model_type = model_type
        self.provider = provider
        self.fields = tuple(fields)
        self._fields_by_column = {field.column_name: field for field in fields}
        struct_type = types.StructType()
        for field in fields:
            struct_type.add_member(field.column_name, field.value_adapter.ydb_type)
        self.struct_type = struct_type

    def get_field_value(self, value: typing.Any, column_name: str) -> typing.Any:
        if not isinstance(value, self.model_type):
            raise ModelConversionError(
                f"Expected {self.model_type.__name__} while converting column {column_name!r}, got {type(value).__name__}"
            )
        field = self._fields_by_column.get(column_name)
        if field is None:
            raise ModelConversionError(f"Column {column_name!r} is not defined by {self.model_type.__name__}")
        return getattr(value, field.attribute_name)

    def from_row(
        self,
        row: typing.Mapping[str, typing.Any],
        *,
        strict_columns: bool,
        path: typing.Optional[str] = None,
    ) -> typing.Any:
        if not isinstance(row, typing.Mapping):
            raise ModelConversionError(f"Expected a mapping for {self.model_type.__name__}, got {type(row).__name__}")
        row_columns = set(row)
        model_columns = set(self._fields_by_column)
        if strict_columns:
            extra = row_columns - model_columns
            if extra:
                raise ModelConversionError(
                    f"Unexpected columns for {self.model_type.__name__}: {', '.join(sorted(extra))}"
                )

        values = {}
        for field in self.fields:
            if field.column_name not in row:
                if field.required:
                    field_path = f"{path}.{field.column_name}" if path else field.column_name
                    raise ModelConversionError(
                        f"Required column {field_path!r} is missing for {self.model_type.__name__}"
                    )
                continue
            field_path = f"{path}.{field.column_name}" if path else field.column_name
            values[field.attribute_name] = field.value_adapter.from_db(row[field.column_name], field_path)
        try:
            return self.provider.construct(values)
        except Exception as error:
            raise ModelConversionError(f"Failed to construct {self.model_type.__name__}: {error}") from error


_ADAPTER_CACHE: "OrderedDict[typing.Tuple[type, typing.Tuple[typing.Tuple[type, bytes], ...]], _ModelAdapter]" = (
    OrderedDict()
)
_ADAPTER_CACHE_LOCK = threading.Lock()
_ADAPTER_CACHE_SIZE = 512


def _mapping_cache_key(type_mapping: typing.Mapping[type, YdbType]) -> typing.Tuple[typing.Tuple[type, bytes], ...]:
    return tuple((python_type, ydb_type.proto.SerializeToString()) for python_type, ydb_type in type_mapping.items())


def get_model_adapter(
    model_type: type,
    type_mapping: typing.Optional[typing.Mapping[type, YdbType]] = None,
) -> _ModelAdapter:
    validate_type_mapping(type_mapping)
    normalized_mapping = dict(type_mapping or {})
    cache_key = (model_type, _mapping_cache_key(normalized_mapping))
    with _ADAPTER_CACHE_LOCK:
        cached = _ADAPTER_CACHE.get(cache_key)
        if cached is not None:
            _ADAPTER_CACHE.move_to_end(cache_key)
            return cached

    adapter = _compile_model_adapter(model_type, normalized_mapping, set())
    with _ADAPTER_CACHE_LOCK:
        _ADAPTER_CACHE[cache_key] = adapter
        _ADAPTER_CACHE.move_to_end(cache_key)
        if len(_ADAPTER_CACHE) > _ADAPTER_CACHE_SIZE:
            _ADAPTER_CACHE.popitem(last=False)
    return adapter


def try_get_model_adapter(
    model_type: type,
    type_mapping: typing.Optional[typing.Mapping[type, YdbType]] = None,
) -> typing.Optional[_ModelAdapter]:
    if _model_provider(model_type) is None:
        return None
    return get_model_adapter(model_type, type_mapping)


def get_value_adapter(
    annotation: typing.Any,
    type_mapping: typing.Optional[typing.Mapping[type, YdbType]] = None,
) -> _ValueAdapter:
    validate_type_mapping(type_mapping)
    annotation, metadata = _unwrap_annotated(annotation)
    explicit_type = metadata.ydb_type if metadata is not None else None
    return _compile_value_adapter(annotation, dict(type_mapping or {}), set(), explicit_type)


def _compile_model_adapter(
    model_type: type,
    type_mapping: typing.Mapping[type, YdbType],
    stack: typing.Set[type],
) -> _ModelAdapter:
    provider = _model_provider(model_type)
    if provider is None:
        raise ModelDefinitionError(f"{model_type!r} is neither a dataclass nor a Pydantic model")
    if model_type in stack:
        raise ModelDefinitionError(f"Recursive model {model_type.__name__} is not supported")
    stack.add(model_type)
    try:
        result = []
        used_columns = set()
        for field in provider.fields():
            annotation, metadata = _unwrap_annotated(field.annotation)
            column_name = metadata.column_name if metadata is not None and metadata.column_name else field.name
            if column_name in used_columns:
                raise ModelDefinitionError(f"Duplicate YDB column {column_name!r} in model {model_type.__name__}")
            used_columns.add(column_name)
            explicit_type = metadata.ydb_type if metadata is not None else None
            value_adapter = _compile_value_adapter(annotation, type_mapping, stack, explicit_type)
            result.append(_ModelFieldSpec(field.name, column_name, value_adapter, field.required))
        return _ModelAdapter(model_type, provider, result)
    finally:
        stack.remove(model_type)


def _compile_value_adapter(
    annotation: typing.Any,
    type_mapping: typing.Mapping[type, YdbType],
    stack: typing.Set[type],
    explicit_type: typing.Optional[YdbType] = None,
) -> _ValueAdapter:
    annotation, nested_metadata = _unwrap_annotated(annotation)
    if nested_metadata is not None and explicit_type is None:
        explicit_type = nested_metadata.ydb_type
    if explicit_type is not None:
        _validate_ydb_type(explicit_type, "ModelField.ydb_type")

    optional_item = _optional_item(annotation)
    if optional_item is not None:
        explicit_item_type = explicit_type.item if isinstance(explicit_type, types.OptionalType) else None
        item_adapter = _compile_value_adapter(optional_item, type_mapping, stack, explicit_item_type)
        ydb_type = explicit_type or types.OptionalType(item_adapter.ydb_type)
        return _ValueAdapter(annotation, ydb_type, "optional", item=item_adapter)

    origin = typing.get_origin(annotation)
    arguments = typing.get_args(annotation)
    if origin is list:
        if len(arguments) != 1:
            raise ModelDefinitionError(f"List field {annotation!r} must have exactly one item type")
        item_adapter = _compile_value_adapter(arguments[0], type_mapping, stack)
        ydb_type = explicit_type or types.ListType(item_adapter.ydb_type)
        return _ValueAdapter(annotation, ydb_type, "list", item=item_adapter)
    if origin is dict:
        if len(arguments) != 2:
            raise ModelDefinitionError(f"Dict field {annotation!r} must have key and value types")
        key_adapter = _compile_value_adapter(arguments[0], type_mapping, stack)
        payload_adapter = _compile_value_adapter(arguments[1], type_mapping, stack)
        ydb_type = explicit_type or types.DictType(key_adapter.ydb_type, payload_adapter.ydb_type)
        return _ValueAdapter(annotation, ydb_type, "dict", key=key_adapter, payload=payload_adapter)

    provider = _model_provider(annotation)
    if provider is not None:
        model_adapter = _compile_model_adapter(annotation, type_mapping, stack)
        ydb_type = explicit_type or type_mapping.get(annotation) or model_adapter.struct_type
        return _ValueAdapter(annotation, ydb_type, "model", model=model_adapter)

    primitive_ydb_type = explicit_type or type_mapping.get(annotation) or _DEFAULT_TYPE_MAPPING.get(annotation)
    if primitive_ydb_type is None:
        raise ModelDefinitionError(
            f"Could not map Python annotation {annotation!r} to a YDB type; "
            "use ModelField(ydb_type=...) or DriverConfig(type_mapping=...)"
        )
    _validate_ydb_type(primitive_ydb_type, "Resolved type mapping")
    return _ValueAdapter(annotation, primitive_ydb_type, "primitive")


def _coerce_primitive(value: typing.Any, annotation: typing.Any, ydb_type: YdbType) -> typing.Any:
    if annotation is datetime.datetime and not isinstance(value, datetime.datetime):
        if ydb_type in (types.PrimitiveType.Timestamp, types.PrimitiveType.Timestamp64):
            return datetime.datetime(1970, 1, 1) + datetime.timedelta(microseconds=value)
        if ydb_type in (types.PrimitiveType.Datetime, types.PrimitiveType.Datetime64):
            return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=value)
    if annotation is datetime.date and not isinstance(value, datetime.date):
        return datetime.date(1970, 1, 1) + datetime.timedelta(days=value)
    if annotation is datetime.timedelta and not isinstance(value, datetime.timedelta):
        return datetime.timedelta(microseconds=value)
    if annotation is uuid.UUID and not isinstance(value, uuid.UUID):
        return uuid.UUID(str(value))
    return value
