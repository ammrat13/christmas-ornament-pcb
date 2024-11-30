//! Module housing all the functionality needed to communicate with the
//! christmas ornament over BLE.

use std::time::Duration;

use anyhow::{Context, Result};
use btleplug::api::{Central, Manager as _, Peripheral as _, ScanFilter, Service};
use btleplug::platform::{Adapter, Manager, Peripheral};
use uuid::Uuid;

#[allow(dead_code)]
static ORNAMENT_SERVICE_UUID: Uuid = Uuid::from_u128(0x895225feacaf4f21b0e71adb51e11653u128);

/// Connect to the christmas ornament, given its display `name`.
pub async fn connect(name: &str, scan_duration: &Duration) -> Result<Peripheral> {
    // See: https://github.com/deviceplug/btleplug/blob/master/examples/discover_adapters_peripherals.rs

    // Get a list of BLE adapters from the OS
    let manager = Manager::new()
        .await
        .context("Failed to retreive bluetooth manager")?;
    let adapters = manager
        .adapters()
        .await
        .context("Failed to retreive bluetooth adapters")?;
    // We don't know which adapter to use, and we don't have a
    // platform-independent way of getting the user to choose, so we'll just use
    // the first one
    let adapter = adapters.get(0).context("No bluetooth adapters found")?;

    // See if we can find the ornament before we start scanning
    let mut ornament = try_find(name, &adapter).await?;

    // If we didn't find the ornament, scan for it
    if ornament.is_none() {
        log::debug!("Could not find the christmas ornament in pre-existing peripherals");
        log::info!("Starting to scan for peripherals");

        adapter
            .start_scan(ScanFilter::default())
            .await
            .context("Failed to start scan")?;
        tokio::time::sleep(*scan_duration).await;
        adapter.stop_scan().await.context("Failed to stop scan")?;
        log::info!("Done scanning for peripherals");

        ornament = try_find(name, &adapter).await?;
    }

    // If we still didn't find the ornament, give up
    let ornament = ornament.context("Could not find the christmas ornament")?;

    // Connect if needed
    if !ornament.is_connected().await? {
        log::debug!("The christmas ornament is not connected");
        log::info!("Connecting to the christmas ornament");
        ornament
            .connect()
            .await
            .context("Could not connect to the christmas ornament")?;
    }

    // Populate the ornament's services
    ornament
        .discover_services()
        .await
        .context("Could not discover services")?;
    log::debug!("Discovered services on the christmas ornament");

    log::info!("Connected to the christmas ornament");
    Ok(ornament)
}

/// Try to find the christmas ornament in the list of peripherals returned by
/// the `adapter`, given its display `name`. May fail. If successful, returns
/// the `Peripheral`, or `None` if it doesn't exist.
async fn try_find(name: &str, adapter: &Adapter) -> Result<Option<Peripheral>> {
    // Extract the peripheral list from the adapter
    let peripherals = adapter
        .peripherals()
        .await
        .context("Could not to get pre-existing peripherals")?;

    // Try to find a peripheral with the given name
    for periph in peripherals {
        let props = periph
            .properties()
            .await
            .context("Could not get peripheral properties")?
            .context("No peripheral properties available")?;
        if props.local_name == Some(name.to_string()) {
            log::debug!("Found the christmas ornament: {:?}", periph);
            return Ok(Some(periph));
        }
    }
    // Couldn't find it, but that's not an error
    Ok(None)
}

/// Get the service with the ornament's service UUID from the `ornament`. Fails
/// if the service is not found.
pub fn get_service(ornament: &Peripheral) -> Result<Service> {
    ornament
        .services()
        .iter()
        .find(|s| s.uuid == ORNAMENT_SERVICE_UUID)
        .context("Could not find the christmas ornament's service")
        .cloned()
}
