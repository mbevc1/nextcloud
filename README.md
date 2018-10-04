# Nextcloud

Nextcloud community contributed RPM packaging.

## Usage

To build RPM using Docker:
```bash
make pkg-docker
```

To build RPM using local Mock installation:
```make
make rpm
```

To get other options you can use: `make help`

Make sure to include the Gzip middleware above any other middleware that alter
the response body.

## Tips

Produced RPM are saved to `pkg/` folder.

## Authors
* [Marko Bevc](https://github.com/mbevc1)

## Contributors and thanks
* [Tobia De Koninck](https://github.com/LEDfan)
* Docker inspiration and scripts: https://github.com/mmornati/docker-mock-rpmbuilder

Check the commit log for a complete list.
