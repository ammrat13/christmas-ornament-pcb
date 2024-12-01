mod attrs;
mod ble;

use std::time::Duration;

use anyhow::{Context, Error, Result};
use argparse::ArgumentParser;
use btleplug::api::Peripheral as _;
use btleplug::platform::Peripheral;
use tokio::net::TcpListener;
use tokio::task::JoinSet;

use attrs::ApplicationState;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let mut local_name = String::from("Christmas Ornament");
    let mut scan_time_s = 15u64;
    let mut disconnect_poll_s = 1u64;
    let mut port = 3000u16;
    {
        let mut ap = ArgumentParser::new();
        ap.set_description("Interface with the Christmas ornament over BLE");
        ap.refer(&mut scan_time_s).metavar("SCAN_TIME").add_option(
            &["-t", "--scan-time"],
            argparse::Store,
            "Time to scan for peripherals for, in seconds",
        );
        ap.refer(&mut disconnect_poll_s)
            .metavar("DISCONNECT_POLL_INTERVAL")
            .add_option(
                &["-d", "--disconnect-poll"],
                argparse::Store,
                "Time to poll for the ornament disconnecting, in seconds",
            );
        ap.refer(&mut port).metavar("PORT").add_option(
            &["-p", "--port"],
            argparse::Store,
            "Port to listen on for HTTP requests",
        );
        ap.refer(&mut local_name)
            .metavar("LOCAL_NAME")
            .required()
            .add_argument(
                "local_name",
                argparse::Store,
                "Display name of the ornament",
            );
        ap.parse_args_or_exit();
    }

    let scan_duration = Duration::from_secs(scan_time_s);
    let poll_duration = Duration::from_secs(disconnect_poll_s);

    let peripheral = ble::connect(&local_name, scan_duration).await?;
    let service = ble::get_service(&peripheral)?;

    let app = attrs::router().with_state(ApplicationState {
        peripheral: peripheral.clone(),
        service: service.clone(),
    });

    let listener = TcpListener::bind(("0.0.0.0", port)).await.unwrap();

    let mut joinset = JoinSet::new();
    joinset.spawn(async { axum::serve(listener, app).await.context("Server died") });
    joinset.spawn(disconnect_handler(peripheral.clone(), poll_duration));

    while let Some(r) = joinset.join_next().await {
        let r = match r {
            Ok(r) => r,
            Err(e) => anyhow::bail!("{:?}", e),
        };
        match r {
            Ok(()) => anyhow::bail!("Some task finished when it was supposed to run forever"),
            Err(e) => anyhow::bail!("{:?}", e),
        }
    }

    // We should always pop some result, so this is unreachable
    unreachable!();
}

/// What to do when the peripheral disconnects from us. We'll poll this every
/// second, and cause an error if that happens.
async fn disconnect_handler(peripheral: Peripheral, poll_interval: Duration) -> Result<(), Error> {
    loop {
        tokio::time::sleep(poll_interval).await;
        if peripheral.is_connected().await? {
            continue;
        }
        anyhow::bail!("Peripheral disconnected");
    }
}
