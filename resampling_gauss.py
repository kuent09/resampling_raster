import json
import logging
import sys
import os
from pathlib import Path

import rasterio
from rasterio.warp import Resampling
from rasterio.transform import Affine

LOG_FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=LOG_FORMAT)


def resampling(input_raster, output_raster, pixel_per_meter):

    with rasterio.open(input_raster) as dataset:

        pixel_per_meter = float(pixel_per_meter)
        ratio = dataset.transform[0] / float(pixel_per_meter)

        data = dataset.read(
            out_shape=(dataset.count, int(dataset.height * ratio), int(dataset.width * ratio)),
            resampling=Resampling.gauss
        )

        transf = Affine(
            pixel_per_meter,
            dataset.transform[1],
            dataset.transform[2],
            dataset.transform[3],
            -pixel_per_meter,
            dataset.transform[5]
        )

        with rasterio.open(
            output_raster,
            "w",
            driver="GTiff",
            height=data.shape[1],
            width=data.shape[2],
            count=dataset.count,
            compress='lzw',
            dtype=data.dtype,
            crs=dataset.crs,
            transform=transf,
            nodata=dataset.nodata
        ) as dst:
            dst.write(data)


def load_inputs(input_path):
    inputs_desc = json.load(open(input_path))
    inputs = inputs_desc.get('inputs')
    parameters = inputs_desc.get('parameters')
    return inputs, parameters


def main():
    WORKING_DIR = os.getenv('DELAIRSTACK_PROCESS_WORKDIR')
    if not WORKING_DIR:
        raise KeyError('DELAIRSTACK_PROCESS_WORKDIR environment variable must be defined')
    WORKING_DIR = Path(WORKING_DIR).resolve()

    logging.debug('Extracting inputs and parameters...')

    # Retrieve inputs and parameters from inputs.json
    inputs, parameters = load_inputs(WORKING_DIR / 'inputs.json')

    # Get info for the inputs
    input_raster = inputs.get('input_raster')
    name = input_raster["name"]
    input_raster_path = inputs['input_raster']['components'][0]['path']
    logging.info(f'Input raster is {name} id: {input_raster["id"]}')

    ratio = parameters.get('pixel_per_meter')
    logging.info(f'Pixel per meter: {ratio}')

    # Create the output raster
    logging.debug('Creating the output raster')
    out_name = name + '_resampled'
    output_raster_path = WORKING_DIR / out_name
    logging.info(f'Output path: {output_raster_path}')

    # Resampling raster
    logging.info('Resampling raster')
    resampling(
        input_raster=input_raster_path,
        output_raster=output_raster_path,
        pixel_per_meter=ratio,
    )

    # Create the outputs.json to describe the deliverable and its path
    logging.debug('Creating the outputs.json')
    output = {
        "outputs": {
            "output_raster": {  # Must match the name of deliverable in yaml
                "type": "raster",
                "format": "tif",
                "name": out_name,
                "components": [
                    {
                        "name": "raster",
                        "path": str(output_raster_path)
                    }
                ]
            },
        },
        "version": "0.1"
    }
    with open(WORKING_DIR / 'outputs.json', 'w+') as f:
        json.dump(output, f)

    logging.info('End of processing.')


if __name__ == "__main__":
    main()
