//! Functions for reading and writing all of the characteristics of the
//! christmas ornament. We call them "attributes" to distinguish them from the
//! actual BLE characteristics. Here, we implement the logic for `GET` and
//! `POST` requests.

mod uintqty;

use axum::http::StatusCode;
use axum::routing::get;
use axum::{Json, Router};
use btleplug::api::Service;
use btleplug::platform::Peripheral;

use crate::ble;

/// The objects each method requires to do its job.
#[derive(Clone)]
pub struct ApplicationState {
    pub peripheral: Peripheral,
    pub service: Service,
}

/// Create a new router that handles all of the attribute routes. Modify this if
/// a new attribute is added.
pub fn router() -> Router<ApplicationState> {
    Router::new().route("/heap_free", get(get_heap_free))
}

/// Utility method for the common task of reading a characteristic and returning
/// its bytes, given its 16-bit UUID.
pub async fn read_characteristic<T>(
    state: &ApplicationState,
    uuid16: u16,
) -> Result<Vec<u8>, (StatusCode, Json<Option<T>>)> {
    // First, convert the 16-bit UUID to a 128-bit UUID
    let uuid = ble::uuid_16(uuid16);
    log::info!("Reading characteristic with UUID16 {:04x}", uuid16);

    // Then, get the characteristic from the service
    let characteristic = match ble::find_characteristic(&state.service, uuid) {
        Some(c) => c,
        None => {
            log::error!("Could not find characteristic with UUID16 {:04x}", uuid16);
            return Err((StatusCode::NOT_FOUND, Json(None)));
        }
    };

    // Finally, read the characteristic and return its value
    match ble::read_characteristic(&state.peripheral, characteristic).await {
        Ok(v) => Ok(v),
        Err(_) => {
            log::error!("Could not read characteristic with UUID16 {:04x}", uuid16);
            Err((StatusCode::INTERNAL_SERVER_ERROR, Json(None)))
        }
    }
}

uintqty::get_method!(get_heap_free, 0x0002, 4, "bytes");
