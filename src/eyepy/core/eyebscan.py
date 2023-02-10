from __future__ import annotations

from types import EllipsisType
from typing import List, Optional, TYPE_CHECKING, Union

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from eyepy import config
from eyepy.core.annotations import EyeBscanLayerAnnotation
from eyepy.core.eyemeta import EyeBscanMeta
from eyepy.core.utils import DynamicDefaultDict

if TYPE_CHECKING:
    from eyepy import EyeVolume


class EyeBscan:
    """ """

    def __init__(self, volume: EyeVolume, index: int):
        """

        Args:
            volume: The EyeVolume this B-scan belongs to
            index: The index of this B-scan in the EyeVolume
        """
        self.index = index
        self.volume = volume

        self.layers = DynamicDefaultDict(lambda x: EyeBscanLayerAnnotation(
            self.volume.layers[x], self.index))
        self.area_maps = DynamicDefaultDict(
            lambda x: self.volume.volume_maps[x].data[self.index])

    @property
    def meta(self) -> EyeBscanMeta:
        """ Return the metadata for this B-scan

        Returns: EyeBscanMeta

        """
        return self.volume.meta["bscan_meta"][self.index]

    @property
    def data(self) -> np.ndarray:
        """ Returns the B-scan data as a numpy array

        Returns: np.ndarray

        """
        return self.volume.data[self.index]

    #@property
    #def ascan_maps(self):
    #    """

    #    Returns:

    #    """
    #    raise NotImplementedError
    # return self.volume.ascan_maps[self.index]

    @property
    def shape(self) -> tuple[int, int]:
        """ Shape of the B-scan data

        Returns: Shape tuple (height, width)

        """
        return self.data.shape

    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        layers: Union[bool, list[str]] = False,
        areas: Union[bool, list[str]] = False,
        #ascans=None,
        layer_kwargs: Optional[dict] = None,
        area_kwargs: Optional[dict] = None,
        #ascan_kwargs=None,
        annotations_only=False,
        region: Union[EllipsisType, tuple[slice, slice]] = np.s_[:, :],
    ):
        """ Plot B-scan.

        Annotations such as layers and areas can be overlaid on the image. With plt.legend() you can add a legend for the shown annotations

        Args:
            ax: Axes to plot on. If not provided plot on the current axes (plt.gca()).
            layers: If `True` plot all layers (default: `False`). If a list of strings is given, plot the layers with the given names.
            areas: If `True` plot all areas (default: `False`). If a list of strings is given, plot the areas with the given names.
            annotations_only: If `True` do not plot the B-scan image
            region: Region of the localizer to plot (default: `np.s_[...]`)
            layer_kwargs: Optional keyword arguments for customizing the OCT layers. If `None` default values are used which are {"linewidth": 1, "linestyle": "-"}
            area_kwargs: Optional keyword arguments for customizing area annotions on the B-scan If `None` default values are used which are {"alpha": 0.5}

        Returns: None

        """
        if ax is None:
            ax = plt.gca()

        # Complete region index expression
        if region[0].start is None:
            r0_start = 0
        else:
            r0_start = region[0].start
        if region[1].start is None:
            r1_start = 0
        else:
            r1_start = region[1].start
        if region[0].stop is None:
            r0_stop = self.shape[0]
        else:
            r0_stop = region[0].stop
        if region[1].stop is None:
            r1_stop = self.shape[1]
        else:
            r1_stop = region[1].stop
        region = np.s_[r0_start:r0_stop, r1_start:r1_stop]

        if not layers:
            layers = []
        elif layers is True:
            layers = self.volume.layers.keys()

        if not areas:
            areas = []
        elif areas is True:
            areas = self.volume.volume_maps.keys()

        #if ascans is None:
        #    ascans = []
        #elif ascans is True:
        #    ascans = self.ascan_maps.keys()

        if layer_kwargs is None:
            layer_kwargs = config.layer_kwargs
        else:
            layer_kwargs = {**config.layer_kwargs, **layer_kwargs}

        if area_kwargs is None:
            area_kwargs = config.area_kwargs
        else:
            area_kwargs = {**config.area_kwargs, **area_kwargs}

        #if ascan_kwargs is None:
        #    ascan_kwargs = config.area_kwargs
        #else:
        #    ascan_kwargs = {**config.ascan_kwargs, **ascan_kwargs}

        if not annotations_only:
            ax.imshow(self.data[region], cmap="gray")

        #for ascan_annotation in ascans:
        #    data = self.ascan_maps[ascan_annotation]
        #    data = np.repeat(np.reshape(data, (1, -1)), self.shape[0], axis=0)
        #    visible = np.zeros(data.shape)
        #    visible[data] = 1.0
        #    ax.imshow(data[region],
        #              alpha=visible[region] * ascan_kwargs["alpha"],
        #              cmap="Reds")

        for area in areas:
            data = self.area_maps[area][region]
            visible = np.zeros(data.shape, dtype=bool)
            visible[data != 0] = 1.0

            meta = self.volume.volume_maps[area].meta
            color = meta["color"] if "color" in meta else "red"
            color = mcolors.to_rgba(color)
            # create a 0 radius circle patch as dummy for the area label
            patch = mpatches.Circle((0, 0), radius=0, color=color, label=area)
            ax.add_patch(patch)

            # Create plot_data by tiling the color vector over the plotting shape
            plot_data = np.tile(np.array(color), data.shape + (1, ))
            # Now turn the alpha channel 0 where the mask is 0 and adjust the remaining alpha
            plot_data[..., 3] *= visible * area_kwargs["alpha"]

            ax.imshow(
                plot_data,
                interpolation="none",
            )
        for layer in layers:
            color = config.layer_colors[layer]

            layer_data = self.layers[layer].data
            # Adjust layer height to plotted region
            layer_data = layer_data - region[0].start
            # Remove layer if outside of region
            layer_data = layer_data[region[1].start:region[1].stop]
            layer_data[layer_data < 0] = 0
            region_height = region[0].stop - region[0].start
            layer_data[layer_data > region_height] = region_height

            ax.plot(
                layer_data,
                color="#" + color,
                label=layer,
                **layer_kwargs,
            )