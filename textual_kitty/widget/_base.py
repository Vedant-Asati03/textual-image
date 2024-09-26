"""Provides a Textual `Widget` to render images in the terminal."""

from pathlib import Path
from typing import Literal, Tuple, Type, cast, override

from PIL import Image as PILImage
from textual.app import RenderResult
from textual.css.styles import RenderStyles
from textual.geometry import Size
from textual.widget import Widget

from textual_kitty.geometry import ImageSize
from textual_kitty.pixeldata import PixelMeta
from textual_kitty.renderable._protocol import _ImageRenderable
from textual_kitty.terminal import get_terminal_sizes


class Image(Widget):
    """Textual `Widget` to render images in the terminal."""

    Renderable: Type[_ImageRenderable]

    def __init_subclass__(cls, Renderable: Type[_ImageRenderable]) -> None:
        cls.Renderable = Renderable

    def __init__(
        self,
        image: str | Path | PILImage.Image | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialized the `Image`.

        Args:
            image: Path to an image file or `PIL.Image.Image` instance with the image data to render.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._renderable: _ImageRenderable | None = None
        self.image = image

    @property
    def image(self) -> str | Path | PILImage.Image | None:
        """The image to render.

        Path to an image file or `PIL.Image.Image` instance with the image data to render.
        """
        return self._image

    @image.setter
    def image(self, value: str | Path | PILImage.Image | None) -> None:
        if self._renderable:
            self._renderable.cleanup()
            self._renderable = None

        self._image = value

        if value:
            pixel_meta = PixelMeta(value)
            self._image_width = pixel_meta.width
            self._image_height = pixel_meta.height
        else:
            self._image_width = 0
            self._image_height = 0

        self.refresh()

    @override
    def render(self) -> RenderResult:
        assert self._image  # Should never happen, as Textual isn't supposed to call this while we report a size of 0

        if self._renderable:
            self._renderable.cleanup()
            self._renderable = None

        self._renderable = self.Renderable(self._image, *self._get_styled_size())
        return self._renderable

    @override
    def get_content_width(self, container: Size, viewport: Size) -> int:
        styled_width, styled_height = self._get_styled_size()
        terminal_sizes = get_terminal_sizes()
        width, _ = ImageSize(
            self._image_width, self._image_height, width=styled_width, height=styled_height
        ).get_cell_size(container.width, container.height, terminal_sizes)
        return width

    @override
    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        styled_width, styled_height = self._get_styled_size()
        terminal_sizes = get_terminal_sizes()
        _, height = ImageSize(
            self._image_width, self._image_height, width=styled_width, height=styled_height
        ).get_cell_size(width, container.height, terminal_sizes)
        return height

    def _get_styled_size(self) -> Tuple[None | Literal["auto"] | int, None | Literal["auto"] | int]:
        width = self._get_styled_dimension(self.styles, "width")
        height = self._get_styled_dimension(self.styles, "height")
        return width, height

    def _get_styled_dimension(
        self, styles: RenderStyles, dimension: Literal["width", "height"]
    ) -> None | Literal["auto"] | int:
        style = getattr(styles, dimension)
        if style is None:
            return None
        elif style.is_auto:
            return "auto"
        else:
            return cast(int, getattr(self.content_size, dimension))