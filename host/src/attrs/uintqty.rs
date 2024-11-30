//! Attributes that represent unsigned integer quantities. These are an unsigned
//! integers that optionally have a unit.

use axum::http::StatusCode;
use axum::Json;
use serde::Serialize;

use crate::attrs;
use crate::attrs::ApplicationState;

/// An unsigned integer quantity with an optional unit. This is the type that is
/// returned by the `GET` methods and ingested by `POST` methods.
#[derive(Serialize)]
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

    // Convert the value to a number. Note that the returned bytes are
    // little-endian.
    let mut num = 0u64;
    for byte in bytes.iter() {
        num <<= 8;
        num |= Into::<u64>::into(*byte);
    }

    (
        StatusCode::OK,
        Json(Some(UIntQtyValue { value: num, unit })),
    )
}
