from __future__ import annotations

import warnings
from collections import abc, namedtuple
from functools import partialmethod
from pathlib import Path
from typing import Any, Iterator, Optional, Type

import _tkinter as tk
from PIL import Image  # type: ignore

from ._base import BaseWidget, CgetAndConfigure, TkWidget
from ._constants import _cursor_styles, _inactive_cursor_styles, _wraps
from ._font import Font
from ._images import Icon
from ._misc import Color, ScreenDistance
from ._utils import (
    ClassPropertyMetaClass,
    _images,
    _text_tags,
    classproperty,
    counts,
    py_to_tcl_arguments,
    update_before,
)
from ._variables import Integer
from .exceptions import TclError
from .scrollbar import Scrollbar


class Tag(CgetAndConfigure, metaclass=ClassPropertyMetaClass):
    _widget: TextBox
    _keys = {
        "bg_color": (Color, "background"),
        "fg_color": (Color, "foreground"),
        "first_line_margin": (ScreenDistance, "lmargin1"),
        "font": Font,
        "hanging_line_margin": (ScreenDistance, "lmargin2"),
        "hidden": (bool, "elide"),
        "justify": str,
        "offset": ScreenDistance,
        "right_margin": (ScreenDistance, "rmargin"),
        "right_margin_bg": (ScreenDistance, "rmargincolor"),
        "selection_bg": (Color, "selectbackground"),
        "selection_fg": (Color, "selectforeground"),
        "space_after_paragraph": (ScreenDistance, "spacing3"),
        "space_before_paragraph": (ScreenDistance, "spacing1"),
        "space_before_wrapped_line": (ScreenDistance, "spacing2"),
        "strikethrough_color": (Color, "overstrikefg"),
        "tab_stops": (str, "tabs"),
        "tab_style": (str, "tabstyle"),
        "underline_color": (Color, "underlinefg"),
        "wrap": _wraps,
    }

    def __init__(
        self,
        _name: str = None,
        *,
        bg_color: Optional[Color] = None,
        fg_color: Optional[Color] = None,
        first_line_margin: Optional[int | ScreenDistance] = None,
        font: Optional[Font] = None,
        hanging_line_margin: Optional[int | ScreenDistance] = None,
        hidden: Optional[bool] = None,
        justify: Optional[str] = None,
        offset: Optional[int | ScreenDistance] = None,
        right_margin: Optional[int | ScreenDistance] = None,
        right_margin_bg: Optional[Color] = None,
        selection_bg: Optional[Color] = None,
        selection_fg: Optional[Color] = None,
        space_after_paragraph: Optional[int | ScreenDistance] = None,
        space_before_paragraph: Optional[int | ScreenDistance] = None,
        space_before_wrapped_line: Optional[int | ScreenDistance] = None,
        strikethrough_color: Optional[Color] = None,
        tab_stops: Optional[tuple[str | int, ...]] = None,
        tab_style: Optional[str] = None,
        underline_color: Optional[Color] = None,
        wrap: Optional[str] = None,
    ) -> None:
        self._name = _name or f"{self._widget.tcl_path}:tag_{next(counts['textbox_tag'])}"
        _text_tags[self._name] = self

        if not font:
            font = self._widget.font.copy()

        self._tcl_call(
            None,
            self,
            "configure",
            background=bg_color,
            elide=hidden,
            font=font,
            foreground=fg_color,
            justify=justify,
            lmargin1=first_line_margin,
            lmargin2=hanging_line_margin,
            offset=offset,
            overstrikefg=strikethrough_color,
            rmargin=right_margin,
            rmargincolor=right_margin_bg,
            selectbackground=selection_bg,
            selectforeground=selection_fg,
            spacing1=space_before_paragraph,
            spacing2=space_before_wrapped_line,
            spacing3=space_after_paragraph,
            tabs=tab_stops,
            tabstyle=tab_style,
            underlinefg=underline_color,
            wrap=_wraps[wrap],
        )

    def __repr__(self) -> str:
        return f"<tukaan.TextBox.Tag named {self._name!r}>"

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._keys.keys():
            self.config(**{key: value})
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key: str) -> Any:
        if key in self._keys.keys():
            return self._cget(key)
        else:
            return super().__getattribute__(key)

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value: str) -> Tag:
        return _text_tags[value]

    def _tcl_call(self, returntype: Any, _dumb_self, subcommand: str, *args, **kwargs) -> Any:
        return self._widget._tcl_call(
            returntype,
            self._widget,
            "tag",
            subcommand,
            self._name,
            *args,
            *py_to_tcl_arguments(**kwargs),
        )

    def add(self, *indexes) -> None:
        self._tcl_call(None, self, "add", *self._widget._get_tcl_index_range(indexes))

    def delete(self) -> None:
        self._tcl_call(None, self, "delete")

    def remove(self, *indexes) -> None:
        self._tcl_call(None, self, "remove", *self._widget._get_tcl_index_range(indexes))

    @property
    def ranges(self):
        result = self._tcl_call((self._widget.index,), self, "ranges")

        for start, end in zip(result[0::2], result[1::2]):
            yield self._widget.range(start, end)

    def _prev_next_range(
        self, direction: str, start: TextIndex, end: Optional[TextIndex] = None
    ) -> None | TextRange:
        if end is None:
            end = {"prev": self._widget.start, "next": self._widget.end}[direction]

        result = self._tcl_call((self._widget.index,), self, f"{direction}range", start, end)

        if not result:
            return None

        return self._widget.range(*result)

    prev_range = partialmethod(_prev_next_range, "prev")
    next_range = partialmethod(_prev_next_range, "next")

    @classproperty
    def hidden(cls) -> Tag:
        return cls.Tag(_name="hidden", hidden=True)

    @classproperty
    def bold(cls) -> Tag:
        font = cls._widget.font.named_copy()
        font.bold = True
        return cls.Tag(font=font)

    @classproperty
    def italic(cls) -> Tag:
        font = cls._widget.font.named_copy()
        font.italic = True
        return cls.Tag(font=font)

    @classproperty
    def underline(cls) -> Tag:
        font = cls._widget.font.named_copy()
        font.underline = True
        return cls.Tag(font=font)

    @classproperty
    def strikethrough(cls) -> Tag:
        font = cls._widget.font.named_copy()
        font.strikethrough = True
        return cls.Tag(font=font)


class TextIndex(namedtuple("TextIndex", ["line", "column"])):
    _widget: TextBox
    __slots__ = ()

    def __new__(cls, *index, no_check=False) -> TextIndex:
        result = None

        if isinstance(index, tuple) and len(index) == 2:
            # line and column numbers
            line, col = index
        else:
            index = index[0]
            if isinstance(index, int):
                if index in {0, 1}:
                    line, col = 1, 0
                elif index == -1:
                    result = cls._widget._tcl_call(
                        str, cls._widget.tcl_path, "index", f"end - 1 chars"
                    )
            elif isinstance(index, tk.Tcl_Obj):
                # Tcl_Obj from _utils.from_tcl()
                result = cls._widget._tcl_call(str, cls._widget.tcl_path, "index", str(index))
            elif isinstance(index, (str, Icon, Image.Image, TkWidget)):
                # string from from_tcl() OR mark name, image name or widget name
                result = cls._widget._tcl_call(str, cls._widget.tcl_path, "index", index)
            elif isinstance(index, tuple):
                line, col = index
            else:
                raise TypeError

        if result:
            line, col = tuple(map(int, result.split(".")))

        if not no_check:
            if (line, col) < tuple(cls._widget.start):
                return cls._widget.start
            if (line, col) > tuple(cls._widget.end):
                return cls._widget.end

        return super(TextIndex, cls).__new__(cls, line, col)  # type: ignore

    def to_tcl(self) -> str:
        return f"{self.line}.{self.column}"

    @classmethod
    def from_tcl(cls, string: str) -> TextIndex:
        return cls(string)

    def _compare(self, other: TextIndex, operator: str) -> bool:
        return self._widget._tcl_call(bool, self._widget, "compare", self, operator, other)

    def __eq__(self, other: TextIndex) -> bool:  # type: ignore[override]
        if not isinstance(other, TextIndex):
            return NotImplemented
        return self._compare(other, "==")

    def __lt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, "<")

    def __gt__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, ">")

    def __le__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, "<=")

    def __ge__(self, other: TextIndex) -> bool:  # type: ignore[override]
        return self._compare(other, ">=")

    def __add__(self, indices: int) -> TextIndex:  # type: ignore[override]
        return self.forward(indices=indices)

    def __sub__(self, indices: int) -> TextIndex:  # type: ignore[override]
        return self.back(indices=indices)

    def clamp(self) -> TextIndex:
        if self < self._widget.start:
            return self._widget.start
        if self > self._widget.end:
            return self._widget.end
        return self

    def _move(self, dir, chars, indices, lines):
        move_str = ""
        if chars:
            move_str += f" {dir} {chars} chars"
        if indices:
            move_str += f" {dir} {indices} indices"
        if lines:
            move_str += f" {dir} {lines} lines"

        return self.from_tcl(self.to_tcl() + move_str).clamp()

    def forward(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self._move("+", chars, indices, lines)

    def back(self, chars: int = 0, indices: int = 0, lines: int = 0) -> TextIndex:
        return self._move("-", chars, indices, lines)

    def _apply_suffix(self, suffix) -> TextIndex:
        return self.from_tcl(f"{self.to_tcl()} {suffix}").clamp()

    @property
    def linestart(self) -> TextIndex:
        return self._apply_suffix("linestart")

    @property
    def lineend(self) -> TextIndex:
        return self._apply_suffix("lineend")

    @property
    def wordstart(self) -> TextIndex:
        return self._apply_suffix("wordstart")

    @property
    def wordend(self) -> TextIndex:
        return self._apply_suffix("wordend")


class TextRange(namedtuple("TextRange", ["start", "end"])):
    _widget: TextBox

    def __new__(
        cls, *indexes: slice | tuple[tuple[int, int], tuple[int, int]] | tuple[TextIndex, TextIndex]
    ) -> TextRange:
        if isinstance(indexes[0], slice):
            start, stop = indexes[0].start, indexes[0].stop
        else:
            start, stop = indexes

        if isinstance(start, tuple):
            start = cls._widget.index(*start)

        if isinstance(stop, tuple):
            stop = cls._widget.index(*stop)

        if start is None:
            start = cls._widget.start

        if stop is None:
            stop = cls._widget.end

        return super(TextRange, cls).__new__(cls, start, stop)  # type: ignore

    def get(self):
        return self._widget.get(self)

    def __contains__(self, index: TextIndex):  # type: ignore[override]
        return self.start <= index < self.end


class TextMarks(abc.MutableMapping):
    _widget: TextBox
    __slots__ = "_widget"

    def __get_names(self) -> list[str]:
        return self._widget._tcl_call([str], self._widget.tcl_path, "mark", "names")

    def __iter__(self) -> Iterator:
        return iter(self.__get_names())

    def __len__(self) -> int:
        return len(self.__get_names())

    def __contains__(self, mark: object) -> bool:
        return mark in self.__get_names()

    def __setitem__(self, name: str, index: TextIndex) -> None:
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "set", name, index)

    def __getitem__(self, name: str) -> TextIndex | None:
        if name not in self.__get_names():
            return None

        return self._widget.index(name)

    def __delitem__(self, name: str) -> None:
        if name == "insert":
            raise RuntimeError("can't delete insertion cursor")
        self._widget._tcl_call(None, self._widget.tcl_path, "mark", "unset", name)


class TextHistory:
    _widget: TextBox
    __slots__ = "_widget"

    def call_subcommand(self, *args):
        if self._widget.track_history is False:
            warnings.warn(
                "undoing is disabled on this textbox widget. Use `track_history=True` to enable it.",
                stacklevel=3,
            )
        return self._widget._tcl_call(bool, self._widget, "edit", *args)

    @property
    def can_redo(self):
        return self.call_subcommand("canredo")

    @property
    def can_undo(self):
        return self.call_subcommand("canundo")

    def redo(self, number=1):
        try:
            for i in range(number):
                self.call_subcommand("redo")
        except TclError:
            return

    __rshift__ = redo

    def undo(self, number=1):
        try:
            for i in range(number):
                self.call_subcommand("undo")
        except TclError:
            return

    __lshift__ = undo

    def clear(self):
        self.call_subcommand("reset")

    def add_sep(self):
        self.call_subcommand("separator")

    @property
    def limit(self) -> int:
        return self._widget._tcl_call(int, self._widget, "cget", "-maxundo")

    @limit.setter
    def limit(self, new_limit: int) -> None:
        self._widget._tcl_call(None, self._widget, "configure", "-maxundo", new_limit)


LineInfo = namedtuple("LineInfo", ["x", "y", "width", "height", "baseline"])
RangeInfo = namedtuple(
    "RangeInfo",
    [
        "chars",
        "displayed_chars",
        "displayed_indices",
        "displayed_lines",
        "indices",
        "lines",
        "width",
        "height",
    ],
)


class _textbox_frame(BaseWidget):
    _tcl_class = "ttk::frame"
    _keys: dict[str, Any | tuple[Any, str]] = {}

    def __init__(self, parent) -> None:
        BaseWidget.__init__(self, parent)


class TextBox(BaseWidget):
    index: Type[TextIndex]
    range: Type[TextRange]
    Tag: Type[Tag]
    marks: TextMarks
    history: TextHistory

    _tcl_class = "text"
    _keys = {
        "bg_color": (Color, "background"),
        "cursor_color": (Color, "insertbackground"),
        "cursor_offtime": (int, "insertofftime"),
        "cursor_ontime": (int, "insertontime"),
        "cursor_style": (_cursor_styles, "blockcursor"),
        "cursor_width": (ScreenDistance, "insertwidth"),
        "fg_color": (Color, "foreground"),
        "focusable": (bool, "takefocus"),
        "font": Font,
        "height": ScreenDistance,
        "inactive_cursor_style": (_inactive_cursor_styles, "insertunfocussed"),
        "inactive_selection_bg": (Color, "inactiveselectbackground"),
        "on_xscroll": ("func", "xscrollcommand"),
        "on_yscroll": ("func", "yscrollcommand"),
        "resize_along_chars": (bool, "setgrid"),
        "selection_bg": (Color, "selectbackground"),
        "selection_fg": (Color, "selectforeground"),
        "space_after_paragraph": (ScreenDistance, "spacing3"),
        "space_before_paragraph": (ScreenDistance, "spacing1"),
        "space_before_wrapped_line": (ScreenDistance, "spacing2"),
        "tab_stops": (str, "tabs"),
        "tab_style": (str, "tabstyle"),
        "track_history": (bool, "undo"),
        "width": ScreenDistance,
        "wrap": _wraps,
    }
    # todo: padding cget, configure

    def __init__(
        self,
        parent: Optional[TkWidget] = None,
        bg_color: Optional[Color] = None,
        cursor_color: Optional[Color] = None,
        cursor_offtime: Optional[int] = None,
        cursor_ontime: Optional[int] = None,
        cursor_style: str = "normal",
        cursor_width: Optional[int | ScreenDistance] = None,
        fg_color: Optional[Color] = None,
        focusable: Optional[bool] = None,
        font: Optional[Font] = None,
        height: Optional[int | ScreenDistance] = None,
        inactive_cursor_style: Optional[str] = None,
        inactive_selection_bg: Optional[Color] = None,
        overflow: tuple[bool | str, bool | str] = ("auto", "auto"),
        padding: Optional[int | tuple[int] | tuple[int, int]] = None,
        resize_along_chars: Optional[bool] = None,
        selection_bg: Optional[Color] = None,
        selection_fg: Optional[Color] = None,
        space_after_paragraph: Optional[int | ScreenDistance] = None,
        space_before_paragraph: Optional[int | ScreenDistance] = None,
        space_before_wrapped_line: Optional[int | ScreenDistance] = None,
        tab_stops: Optional[tuple[str | int, ...]] = None,
        tab_style: Optional[str] = None,
        track_history: Optional[bool] = None,
        width: Optional[int | ScreenDistance] = None,
        wrap: Optional[str] = None,
        _peer_of: Optional[TextBox] = None,
    ) -> None:

        if not font:
            font = Font("monospace")

        padx = pady = None
        if padding is not None:
            if isinstance(padding, int):
                padx = pady = padding
            elif len(padding) == 1:
                padx = pady = padding[0]
            elif len(padding) == 2:
                padx, pady = padding
            else:
                raise ValueError(
                    "unfortunately 4 side paddings aren't supported for TextBox padding"
                )

        if cursor_offtime is not None:
            cursor_offtime = int(1000 * cursor_offtime)

        if cursor_ontime is not None:
            cursor_ontime = int(1000 * cursor_ontime)

        self.peer_of = _peer_of

        to_call = {
            "autoseparators": True,
            "highlightthickness": 0,
            "relief": "flat",
            "background": bg_color,
            "blockcursor": _cursor_styles[cursor_style],
            "font": font,
            "foreground": fg_color,
            "height": height,
            "inactiveselectbackground": inactive_selection_bg,
            "insertbackground": cursor_color,
            "insertofftime": cursor_offtime,
            "insertontime": cursor_ontime,
            "insertunfocussed": _inactive_cursor_styles[inactive_cursor_style],
            "insertwidth": cursor_width,
            "padx": padx,
            "pady": pady,
            "selectbackground": selection_bg,
            "selectforeground": selection_fg,
            "setgrid": resize_along_chars,
            "spacing1": space_before_paragraph,
            "spacing2": space_before_wrapped_line,
            "spacing3": space_after_paragraph,
            "tabs": tab_stops,
            "tabstyle": tab_style,
            "takefocus": focusable,
            "undo": track_history,
            "width": width,
            "wrap": _wraps[wrap],
        }

        if _peer_of is None:
            self._frame = _textbox_frame(parent)
            BaseWidget.__init__(self, self._frame, None, **to_call)
        else:
            self._frame = _textbox_frame(_peer_of._frame.parent)
            tcl_path = f"{self._frame.tcl_path}.textbox_peer_{_peer_of.peer_count}_of_{_peer_of.tcl_path.split('.')[-1]}"
            BaseWidget.__init__(
                self, self._frame, (_peer_of, "peer", "create", tcl_path), **to_call
            )
            self.tcl_path = tcl_path

        self.peer_count: int = 0

        self._tcl_eval(
            None,
            f"grid rowconfigure {self._frame.tcl_path} 0 -weight 1 \n"
            + f"grid columnconfigure {self._frame.tcl_path} 0 -weight 1 \n"
            + f"grid {self.tcl_path} -row 0 -column 0 -sticky nsew",
        )
        if overflow is not None:
            self.overflow = overflow

        self.index = TextIndex
        self.range = TextRange
        self.Tag = Tag
        self.marks = TextMarks()
        self.history = TextHistory()
        for attr in (self.index, self.range, self.Tag, self.marks, self.history):
            setattr(attr, "_widget", self)

        self.layout = self._frame.layout

    def _make_hor_scroll(self, hide=True):
        self._h_scroll = Scrollbar(self._frame, orientation="horizontal", auto_hide=hide)
        self._h_scroll.attach(self)
        self._h_scroll.layout.grid(row=1, hor_align="stretch")

    def _make_vert_scroll(self, hide=True):
        self._v_scroll = Scrollbar(self._frame, orientation="vertical", auto_hide=hide)
        self._v_scroll.attach(self)
        self._v_scroll.layout.grid(col=1, vert_align="stretch")

    def Peer(self, **kwargs):
        if self.peer_of is None:
            self.peer_count += 1
            return TextBox(_peer_of=self, **kwargs)
        else:
            raise RuntimeError("can't create a peer of a peer")

    @property
    def start(self) -> TextIndex:
        return self.index(0, no_check=True)

    @property
    def end(self) -> TextIndex:
        return self.index(-1, no_check=True)

    @property
    def current(self) -> TextIndex:
        return self.marks["insert"]

    @current.setter
    def current(self, new_pos: TextIndex) -> None:
        self.marks["insert"] = new_pos

    @property
    def mouse_index(self) -> TextIndex:
        return self.index("current")

    def coord_to_index(self, x, y) -> TextIndex:
        return self.index(f"@{int(x)},{int(y)}")

    def insert(self, index: TextIndex | str = "insert", content: str = "", **kwargs) -> None:
        if isinstance(content, (Image.Image, Icon)):
            margin = kwargs.pop("margin", None)
            padx = pady = None
            if margin:
                if isinstance(margin, int) or len(margin) == 1:
                    padx = pady = margin
                elif len(margin) == 2:
                    padx, pady = margin
                else:
                    raise ValueError(
                        "unfortunately 4 side margins aren't supported for embedded images"
                    )

            align = kwargs.pop("align", None)

            # fmt: off
            to_call = ("image", "create", index, *py_to_tcl_arguments(image=content, padx=padx, pady=pady, align=align))
            # fmt: on
        elif isinstance(content, TkWidget):
            margin = kwargs.pop("margin", None)
            padx = pady = None
            if margin is not None:
                if isinstance(margin, int) or len(margin) == 1:
                    padx = pady = margin
                elif len(margin) == 2:
                    padx, pady = margin
                else:
                    raise ValueError(
                        "unfortunately 4 side margins aren't supported for embedded widgets"
                    )

            align = kwargs.pop("align", None)
            stretch = False
            if align == "stretch":
                stretch = True
                align = None

            # fmt: off
            to_call = ("window", "create", index, *py_to_tcl_arguments(window=content, padx=padx, pady=pady, align=align, stretch=stretch))
            # fmt: on
        elif isinstance(content, Path):
            with open(str(content.resolve())) as file:
                to_call = ("insert", index, file.read())
        else:
            to_call = ("insert", index, content)

        if kwargs:
            raise TypeError(f"insert() got unexpected keyword argument(s): {tuple(kwargs.keys())}")
        self._tcl_call(None, self, *to_call)

    def _get_tcl_index_range(self, indexes):
        if len(indexes) == 1:
            index_or_range = indexes[0]

            if isinstance(index_or_range, self.range):
                return tuple(index.to_tcl() for index in index_or_range)
            elif isinstance(index_or_range, self.index):
                return index_or_range.to_tcl(), index_or_range.forward(chars=1).to_tcl()
            elif isinstance(index_or_range, tuple):
                return (
                    self.index(*index_or_range).to_tcl(),
                    self.index(*index_or_range).forward(chars=1).to_tcl(),
                )
        elif len(indexes) == 2:
            return tuple(index.to_tcl() for index in self.range(*indexes))
        else:
            return "1.0", "end - 1 chars"

    def delete(self, *indexes) -> None:
        self._tcl_call(None, self, "delete", *self._get_tcl_index_range(indexes))

    def get(self, *indexes) -> str:
        return self._tcl_call(str, self, "get", *self._get_tcl_index_range(indexes))

    def replace(self, *args, tag: Optional[Tag] = None) -> None:
        if isinstance(args[0], TextRange) and isinstance(args[1], str):
            start, end = args[0]
            text = args[1]
        elif (
            len(args) == 3
            and isinstance(args[0], self.index)
            and isinstance(args[1], self.index)
            and isinstance(args[2], str)
        ):
            start = self.start if args[0] is None else args[0]
            end = self.end if args[1] is None else args[1]
            text = args[2]
        else:
            raise ValueError("invalid arguments. See help(TextBox.replace).")

        self._tcl_call(None, self, "replace", start, end, text, tag)

    def search(
        self,
        pattern: str,
        start: TextIndex,
        stop: TextIndex | str = "end",
        *,
        backwards: bool = False,
        case_sensitive: bool = True,
        count_hidden: bool = False,
        exact: bool = False,
        forwards: bool = False,
        match_newline: bool = False,
        regex: bool = False,
        strict_limits: bool = False,
        variable: Integer = None,
    ):

        if stop == self.end:
            stop = "end - 1 chars"

        if variable is None:
            variable = Integer()

        to_call: list[str] = []

        if backwards:
            to_call += "-backwards"
        if not case_sensitive:
            to_call += "-nocase"
        if count_hidden:
            to_call += "-elide"
        if exact:
            to_call += "-exact"
        if forwards:
            to_call += "-forwards"
        if match_newline:
            to_call += "-nolinestop"
        if regex:
            to_call += "-regexp"
        if strict_limits:
            to_call += "-strictlimits"

        if pattern and pattern[0] == "-":
            to_call += "--"

        while True:
            result = self._tcl_call(
                str, self.tcl_path, "search", "-count", variable, *to_call, pattern, start, stop
            )
            if not result:
                break
            yield self.range(self.index(result), self.index(result).forward(chars=variable.get()))  # type: ignore
            start = result + "+ 1 chars"

    def scroll_to(self, index: TextIndex) -> None:
        self._tcl_call(None, self, "see", index)

    def x_scroll(self, *args) -> None:
        self._tcl_call(None, self, "xview", *args)

    def y_scroll(self, *args) -> None:
        self._tcl_call(None, self, "yview", *args)

    @property
    def overflow(self) -> tuple[bool | str, bool | str]:
        return self._overflow

    @overflow.setter
    def overflow(self, new_overflow: tuple[bool | str, bool | str]) -> None:
        if hasattr(self, "_h_scroll"):
            self._h_scroll.destroy()
        if hasattr(self, "_v_scroll"):
            self._v_scroll.destroy()

        if len(new_overflow) == 1:
            new_overflow = (new_overflow[0], new_overflow[0])

        if new_overflow == (False, False):
            pass
        elif new_overflow == (True, False):
            self._make_hor_scroll(False)
        elif new_overflow == (False, True):
            self._make_vert_scroll(False)
        elif new_overflow == (True, True):
            self._make_hor_scroll(False)
            self._make_vert_scroll(False)
        elif new_overflow == ("auto", False):
            self._make_hor_scroll()
        elif new_overflow == (False, "auto"):
            self._make_vert_scroll()
        elif new_overflow == ("auto", True):
            self._make_hor_scroll()
            self._make_vert_scroll(False)
        elif new_overflow == (True, "auto"):
            self._make_hor_scroll(False)
            self._make_vert_scroll()
        elif new_overflow == ("auto", "auto"):
            self._make_hor_scroll()
            self._make_vert_scroll()
        else:
            raise ValueError(f"invalid overflow value: {new_overflow}")

        self._overflow = new_overflow

    @property
    def text(self) -> str:
        return self.get()

    @text.setter
    def text(self, new_text: str) -> None:
        self.delete()
        self.insert(self.end, new_text)

    @property
    def content(self) -> list[tuple[TextIndex, str | Tag | Icon | Image.Image | TkWidget]]:
        result = []  # type: ignore
        unclosed_tags = {}

        def add_item(type: str, value: str, index: str) -> None:
            nonlocal result
            nonlocal unclosed_tags

            if type == "tagon":
                unclosed_tags[value] = (index, len(result))
                return
            elif type == "tagoff":
                if value in unclosed_tags:
                    result.insert(
                        unclosed_tags[value][1],
                        (
                            self.range(self.index(unclosed_tags[value][0]), self.index(index)),
                            Tag.from_tcl(value),
                        ),
                    )
                    return

            convert = {
                "image": lambda x: _images[x],
                "mark": lambda x: f"TextBox.marks[{x!r}]",
                "text": str,
                "window": TkWidget.from_tcl,
            }[type]

            result += (self.index(index), convert(value))  # type: ignore  # "object" not callable

        self._tcl_call(str, self, "dump", "-all", "-command", add_item, "1.0", "end - 1 chars")
        return result

    @update_before
    def line_info(self, index: TextIndex) -> LineInfo:
        """Returns the accurate height only if the TextBox widget has already laid out"""
        result = self._tcl_call(
            (ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance, ScreenDistance),
            self,
            "dlineinfo",
            index,
        )

        return LineInfo(*result)

    def range_info(self, *indexes) -> RangeInfo:
        result = self._tcl_call(
            (int, int, int, int, int, int, ScreenDistance, ScreenDistance),
            self,
            "count",
            "-chars",
            "-displaychars",
            "-displayindices",
            "-displaylines",
            "-indices",
            "-lines",
            "-xpixels",
            "-ypixels",
            *self._get_tcl_index_range(indexes),
        )

        return RangeInfo(*result)

    def __matmul__(self, index: tuple[int, int] | int | Icon | Image.Image | TkWidget):
        return self.index(index)

    def __contains__(self, text: str):
        return text in self.get()

    def __getitem__(self, index: slice | tuple | TextBox.index):
        if isinstance(index, slice):
            return self.get(self.range(index))
        elif isinstance(index, (tuple, self.index)):
            return self.get(index)
        raise TypeError("expected a tuple, a slice or a `TextBox.index` object")
