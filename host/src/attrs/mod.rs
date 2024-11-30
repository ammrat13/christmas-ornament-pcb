//! Functions for reading and writing all of the characteristics of the
//! christmas ornament. We call them "attributes" to distinguish them from the
//! actual BLE characteristics. Here, we implement the logic for `GET` and
//! `POST` requests.

use axum::Router;
use btleplug::api::Service;
use btleplug::platform::Peripheral;

/// The objects each method requires to do its job.
#[derive(Clone)]
pub struct ApplicationState {
    pub peripheral: Peripheral,
    pub service: Service,
}

/// Create a new router that handles all of the attribute routes. Modify this if
/// a new attribute is added.
pub fn router() -> Router<ApplicationState> {
    todo!();
}
