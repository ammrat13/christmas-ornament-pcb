//! Functions for reading and writing all of the characteristics of the
//! christmas ornament. We call them "attributes" to distinguish them from the
//! actual BLE characteristics. Here, we implement the logic for `GET` and
//! `POST` requests.

mod scaledqty;
mod uintqty;

use axum::http::StatusCode;
use axum::routing::{get, post};
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
    Router::new()
        .route("/heap", get(get_heap))
        .route("/battery", get(get_battery))
        .route("/bootcount", get(get_bootcount))
        .route("/light", get(get_light))
        .route("/light/threshold", get(get_light_threshold))
        .route("/light/threshold", post(post_light_threshold))
        .route("/accelerometer", get(get_accelerometer))
        .route("/accelerometer/threshold", get(get_accelerometer_threshold))
        .route(
            "/accelerometer/threshold",
            post(post_accelerometer_threshold),
        )
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
        Some(c) => {
            log::debug!("    successfully found characteristic");
            c
        }
        None => {
            log::error!("Could not find characteristic with UUID16 {:04x}", uuid16);
            return Err((StatusCode::NOT_FOUND, Json(None)));
        }
    };

    // Finally, read the characteristic and return its value
    match ble::read_characteristic(&state.peripheral, characteristic).await {
        Ok(v) => {
            log::debug!("    successfully read characteristic");
            Ok(v)
        }
        Err(_) => {
            log::error!("Could not read characteristic with UUID16 {:04x}", uuid16);
            Err((StatusCode::INTERNAL_SERVER_ERROR, Json(None)))
        }
    }
}

/// Utility method for the common task of writing a characteristic's, given its
/// 16-bit UUID and the bytes to write.
pub async fn write_characteristic(
    state: &ApplicationState,
    uuid16: u16,
    value: &[u8],
) -> StatusCode {
    // First, convert the 16-bit UUID to a 128-bit UUID
    let uuid = ble::uuid_16(uuid16);
    log::info!("Writing characteristic with UUID16 {:04x}", uuid16);

    // Then, get the characteristic from the service
    let characteristic = match ble::find_characteristic(&state.service, uuid) {
        Some(c) => {
            log::debug!("    successfully found characteristic");
            c
        }
        None => {
            log::error!("Could not find characteristic with UUID16 {:04x}", uuid16);
            return StatusCode::NOT_FOUND;
        }
    };

    // Finally, write the characteristic and return
    match ble::write_characteristic(&state.peripheral, characteristic, value).await {
        Ok(_) => {
            log::debug!("    successfully wrote characteristic");
            StatusCode::OK
        }
        Err(_) => {
            log::error!("Could not write characteristic with UUID16 {:04x}", uuid16);
            StatusCode::INTERNAL_SERVER_ERROR
        }
    }
}

uintqty::get_method!(get_heap, 0x0002, 4, "bytes");
scaledqty::get_method!(get_battery, 0x0003, 2, 1.00709544518e-4, "volts");
scaledqty::get_method!(get_light, 0x0004, 4, 1e-3, "lux");
uintqty::get_method!(get_accelerometer, 0x0005, 3);
scaledqty::get_method!(get_light_threshold, 0x0006, 4, 1e-1, "lux");
scaledqty::get_method!(get_accelerometer_threshold, 0x0007, 2, 1e-3, "g");

scaledqty::post_method!(post_light_threshold, 0x0008, 4, 1e-1, "lux");
scaledqty::post_method!(post_accelerometer_threshold, 0x0009, 2, 1e-3, "g");

uintqty::get_method!(get_bootcount, 0x0010, 1);
