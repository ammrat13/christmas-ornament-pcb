# Host Code

This program exposes an HTTP server with a RESTful API to communicate with the
christmas ornament over Bluetooth. It will automatically connect to the ornament
on startup.

The endpoints are defined in `crate::attrs::router()`. All methods take and
return JSON objects, with the schemas defined in `UIntQtyValue` and
`ScaledQtyValue` respectively.
