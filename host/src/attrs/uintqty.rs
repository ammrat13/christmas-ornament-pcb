//! Attributes that represent unsigned integer quantities. These are an unsigned
//! integers that optionally have a unit.

use axum::http::StatusCode;
use axum::Json;
use serde::{Deserialize, Serialize};

use crate::attrs;
use crate::attrs::ApplicationState;

/// An unsigned integer quantity with an optional unit. This is the type that is
/// returned by the `GET` methods and ingested by `POST` methods.
#[derive(Deserialize, Serialize)]
pub struct UIntQtyValue {
    pub value: u64,
    pub unit: Option<String>,
}

/// Macro to generate a `GET` method for a characteristic.
macro_rules! get_method {
    ($name:ident, $uuid16:literal, $length:literal, $unit:literal) => {
        async fn $name(
            axum::extract::State(state): axum::extract::State<$crate::attrs::ApplicationState>,
        ) -> (
            axum::http::StatusCode,
            axum::extract::Json<Option<$crate::attrs::uintqty::UIntQtyValue>>,
        ) {
            static_assertions::const_assert!($length != 0);
            static_assertions::const_assert!($length <= 8);
            $crate::attrs::uintqty::get(state, $uuid16, $length, Some(String::from($unit))).await
        }
    };
    ($name:ident, $uuid16:literal, $length:literal) => {
        async fn $name(
            axum::extract::State(state): axum::extract::State<$crate::attrs::ApplicationState>,
        ) -> (
            axum::http::StatusCode,
            axum::extract::Json<Option<$crate::attrs::uintqty::UIntQtyValue>>,
        ) {
            static_assertions::const_assert!($length != 0);
            static_assertions::const_assert!($length <= 8);
            $crate::attrs::uintqty::get(state, $uuid16, $length, None).await
        }
    };
}
pub(crate) use get_method;

/// Generic method for `GET` requests. Other `get_*` methods will call this one.
/// It takes the `uuid` of the characteristic to read, the `length` of the
/// attribute in bytes, and an optional `unit` to attach to the value.
pub async fn get(
    state: ApplicationState,
    uuid16: u16,
    length: usize,
    unit: Option<String>,
) -> (StatusCode, Json<Option<UIntQtyValue>>) {
    // Read the characteristic
    let bytes = match attrs::read_characteristic::<UIntQtyValue>(&state, uuid16).await {
        Ok(v) => v,
        Err(e) => return e,
    };
    // Check that the value is the correct length
    if bytes.len() != length {
        log::error!("Expected {} bytes, but got {}", length, bytes.len());
        return (StatusCode::INTERNAL_SERVER_ERROR, Json(None));
    }

    // Special case: if all the bytes are 0xff, then the value has not yet been
    // set by the ornament.
    if bytes.iter().all(|b| *b == 0xff) {
        return (StatusCode::SERVICE_UNAVAILABLE, Json(None));
    }

    // Convert the value to a number. Note that the returned bytes are
    // little-endian.
    let mut num = 0u64;
    for byte in bytes.iter() {
        num <<= 8;
        num |= Into::<u64>::into(*byte);
    }
    log::debug!("Characteristic {:04x} - {}", uuid16, num);

    (
        StatusCode::OK,
        Json(Some(UIntQtyValue { value: num, unit })),
    )
}

/// Macro to generate a `POST` method for a characteristic.
macro_rules! post_method {
    ($name:ident, $uuid16:literal, $length:literal, $unit:literal) => {
        async fn $name(
            axum::extract::State(state): axum::extract::State<$crate::attrs::ApplicationState>,
            axum::extract::Json(request): axum::extract::Json<$crate::attrs::uintqty::UIntQtyValue>,
        ) -> axum::http::StatusCode {
            static_assertions::const_assert!($length != 0);
            static_assertions::const_assert!($length <= 8);
            $crate::attrs::uintqty::post(state, request, $uuid16, $length, Some(String::from($unit))).await
        }
    };
    ($name:ident, $uuid16:literal, $length:literal) => {
        async fn $name(
            axum::extract::State(state): axum::extract::State<$crate::attrs::ApplicationState>,
            axum::extract::Json(request): axum::extract::Json<$crate::attrs::uintqty::UIntQtyValue>,
        ) -> axum::http::StatusCode {
            static_assertions::const_assert!($length != 0);
            static_assertions::const_assert!($length <= 8);
            $crate::attrs::uintqty::post(state, request, $uuid16, $length, None).await
        }
    };
}
pub(crate) use post_method;

/// Generic method for `POST` requests. Other `post_*` methods will call this
/// one. The units of the request must match the `unit` of the characteristic.
pub async fn post(
    state: ApplicationState,
    request: UIntQtyValue,
    uuid16: u16,
    length: usize,
    unit: Option<String>,
) -> StatusCode {
    // Check that the unit matches the characteristic
    if unit != request.unit {
        log::error!(
            "Expected unit {:?}, but got {:?}",
            unit.as_deref(),
            request.unit
        );
        return StatusCode::BAD_REQUEST;
    }

    // Convert the value to bytes. Note that the bytes are little-endian.
    let mut bytes = Vec::with_capacity(length);
    let mut num = request.value;
    for _ in 0..length {
        bytes.push((num & 0xff) as u8);
        num >>= 8;
    }
    // If we have any leftover bytes, then the value is too large
    if num != 0 {
        log::error!("Value is too large for {} bytes: {}", length, request.value);
        return StatusCode::BAD_REQUEST;
    }
    // If all the bytes are 0xff, then the value is invalid
    if bytes.iter().all(|b| *b == 0xff) {
        log::error!("Value is the invalid marker: {}", request.value);
        return StatusCode::BAD_REQUEST;
    }

    // Write the characteristic
    attrs::write_characteristic(&state, uuid16, &bytes).await
}
