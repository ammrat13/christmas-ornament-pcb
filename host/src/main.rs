mod attrs;
mod ble;

use std::time::Duration;

use anyhow::Result;
use argparse::ArgumentParser;
use tokio::net::TcpListener;

use attrs::ApplicationState;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let mut local_name = String::from("Christmas Ornament");
    let mut scan_time_s = 15u64;
    let mut port = 3000u16;
    {
        let mut ap = ArgumentParser::new();
        ap.set_description("Interface with the Christmas ornament over BLE");
        ap.refer(&mut scan_time_s).metavar("SCAN_TIME").add_option(
            &["-t", "--scan-time"],
            argparse::Store,
            "Time to scan for peripherals in seconds",
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

    let peripheral = ble::connect(&local_name, &Duration::from_secs(scan_time_s)).await?;
    let service = ble::get_service(&peripheral)?;

    let app = attrs::router().with_state(ApplicationState {
        peripheral,
        service,
    });

    let listener = TcpListener::bind(("0.0.0.0", port)).await.unwrap();
    axum::serve(listener, app).await?;

    anyhow::bail!("The server should never exit");
}
