//! Attributes that represent floating-point quantities, that are encoded as
//! fixed-point integers. The unit is not optional.
//!
//! See crate::attrs::uintqty

use axum::http::StatusCode;
use axum::Json;
use serde::Serialize;

use crate::attrs::uintqty;
use crate::attrs::ApplicationState;

#[derive(Serialize)]
pub struct ScaledQtyValue {
    pub value: f64,
    pub unit: String,
}

/// Macro to generate a `GET` method.
macro_rules! get_method {
    ($name:ident, $uuid16:literal, $length:literal, $scale:literal, $unit:literal) => {
        async fn $name(
            axum::extract::State(state): axum::extract::State<$crate::attrs::ApplicationState>,
        ) -> (
            axum::http::StatusCode,
            axum::extract::Json<Option<$crate::attrs::scaledqty::ScaledQtyValue>>,
        ) {
            static_assertions::const_assert!($length != 0);
            static_assertions::const_assert!($length <= 8);
            $crate::attrs::scaledqty::get(state, $uuid16, $length, $scale, String::from($unit))
                .await
        }
    };
}
pub(crate) use get_method;

/// Generic method for `GET` requests. The only difference between this and the
/// `uintqty::get` method is that this takes a `scale` parameter. This is the
/// amount that `1` is multiplied by to get the actual value. Also, it returns
/// a different type.
pub async fn get(
    state: ApplicationState,
    uuid16: u16,
    length: usize,
    scale: f64,
    unit: String,
) -> (StatusCode, Json<Option<ScaledQtyValue>>) {
    // Call into the `uintqty` module to read the characteristic
    let (resp, val) = uintqty::get(state, uuid16, length, Some(unit.clone())).await;

    // If the value is `None`, just immediately return
    let val = match val {
        Json(None) => return (resp, Json(None)),
        Json(Some(v)) => v,
    };

    // Otherwise, scale the value and return it. Note that units are mandatory.
    let scaled = ScaledQtyValue {
        value: val.value as f64 * scale,
        unit,
    };
    (resp, Json(Some(scaled)))
}
