# Nextcloud

Nextcloud community contributed RPM packaging.

## Usage

To build RPM package (will use Docker):
```bash
make package
```

To build RPM using local devtool:
```make
make buildev
```

To get other options you can use: `make help`

## Tips

Produced RPM are saved to `pkg/` folder.

## Authors
* [Marko Bevc](https://github.com/mbevc1)

## Contributors and thanks
* [Tobia De Koninck](https://github.com/LEDfan)
* Docker inspiration and scripts: https://github.com/mmornati/docker-mock-rpmbuilder

Check the commit log for a complete list.
