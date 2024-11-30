mod ble;

use std::time::Duration;

use anyhow::Result;
use argparse::ArgumentParser;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let mut local_name = String::from("Christmas Ornament");
    let mut scan_time_s = 15u64;
    {
        let mut ap = ArgumentParser::new();
        ap.set_description("Interface with the Christmas ornament over BLE");
        ap.refer(&mut scan_time_s).metavar("SCAN_TIME").add_option(
            &["-t", "--scan-time"],
            argparse::Store,
            "Time to scan for peripherals in seconds",
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

    let ornament = ble::connect(&local_name, &Duration::from_secs(scan_time_s)).await?;
    let ornament_service = ble::get_service(&ornament)?;
    Ok(())
}
