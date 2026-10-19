#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import pickle
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure


def _load_pickle_with_numpy_compat(path: Path) -> object:
    try:
        with path.open("rb") as handle:
            return pickle.load(handle)
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        numpy_modules = {
            "numpy._core",
            "numpy.core",
            "numpy._core.multiarray",
            "numpy.core.multiarray",
        }
        if missing not in numpy_modules:
            raise
        import importlib

        core_private = None
        core_public = None
        try:
            core_private = importlib.import_module("numpy._core")
        except ModuleNotFoundError:
            pass
        try:
            core_public = importlib.import_module("numpy.core")
        except ModuleNotFoundError:
            pass
        if core_private is not None:
            sys.modules.setdefault("numpy._core", core_private)
            if hasattr(core_private, "multiarray"):
                sys.modules.setdefault("numpy._core.multiarray", core_private.multiarray)
        if core_public is not None:
            sys.modules.setdefault("numpy.core", core_public)
            if hasattr(core_public, "multiarray"):
                sys.modules.setdefault("numpy.core.multiarray", core_public.multiarray)

        with path.open("rb") as handle:
            return pickle.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect pickled matplotlib plots into a single grid figure."
    )
    parser.add_argument("--in-dir", type=Path, default=Path("analysis_2"))
    parser.add_argument("--out", type=Path, default=Path("analysis_2/combined_grid.pdf"))
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--glob", dest="pattern", default="*.pkl")
    parser.add_argument("--show-names", action="store_true", help="Show pickle filename stem as subplot title.")
    return parser.parse_args()


def _extract_plot_axes(obj: object, path: Path) -> tuple[Axes, Figure]:
    if isinstance(obj, Axes):
        ax = obj
        fig = ax.figure
        return ax, fig
    if isinstance(obj, Figure):
        fig = obj
    elif hasattr(obj, "get_figure"):
        fig = obj.get_figure()
    elif hasattr(obj, "figure"):
        fig = obj.figure
    else:
        raise SystemExit(
            f"Unsupported pickle payload in {path}: expected matplotlib Figure or Axes."
        )

    if not isinstance(fig, Figure) or not fig.axes:
        raise SystemExit(f"Pickle in {path} did not contain usable matplotlib axes.")

    # Prefer the non-colorbar axis when both plot axis + colorbar axis are present.
    for ax in fig.axes:
        if ax.get_label() != "<colorbar>":
            return ax, fig
    return fig.axes[0], fig


def _find_colorbar_axis(fig: Figure) -> Axes | None:
    for ax in fig.axes:
        if ax.get_label() == "<colorbar>":
            return ax
    return None


def _copy_lines(src_ax: Axes, dst_ax: Axes) -> None:
    for src_line in src_ax.lines:
        xdata = np.asarray(src_line.get_xdata(orig=False))
        ydata = np.asarray(src_line.get_ydata(orig=False))
        (dst_line,) = dst_ax.plot(xdata, ydata)
        dst_line.update_from(src_line)
        dst_line.set_transform(dst_ax.transData)
        # `update_from` can carry over the source clip path; bind clipping to the
        # destination axes so lines remain visible in every subplot.
        dst_line.set_clip_path(dst_ax.patch)


def _copy_path_collections(src_ax: Axes, dst_ax: Axes) -> PathCollection | None:
    first_mappable: PathCollection | None = None
    for src_coll in src_ax.collections:
        if not isinstance(src_coll, PathCollection):
            continue
        offsets = np.asarray(src_coll.get_offsets())
        if offsets.size == 0:
            continue
        x = offsets[:, 0]
        y = offsets[:, 1]
        kwargs: dict[str, object] = {}
        sizes = np.asarray(src_coll.get_sizes())
        if sizes.size:
            kwargs["s"] = sizes
        arr = src_coll.get_array()
        if arr is not None and np.asarray(arr).size == offsets.shape[0]:
            kwargs["c"] = np.asarray(arr)
            kwargs["cmap"] = src_coll.get_cmap()
            kwargs["norm"] = src_coll.norm
        else:
            facecolors = src_coll.get_facecolors()
            if facecolors is not None and len(facecolors):
                kwargs["c"] = facecolors
        edgecolors = src_coll.get_edgecolors()
        if edgecolors is not None and len(edgecolors):
            kwargs["edgecolors"] = edgecolors
        linewidths = src_coll.get_linewidths()
        if linewidths is not None and len(linewidths):
            kwargs["linewidths"] = linewidths
        alpha = src_coll.get_alpha()
        if alpha is not None:
            kwargs["alpha"] = alpha
        paths = src_coll.get_paths()
        if paths:
            kwargs["marker"] = paths[0]
        dst_coll = dst_ax.scatter(x, y, **kwargs)
        dst_coll.set_zorder(src_coll.get_zorder())
        dst_coll.set_rasterized(False)
        if first_mappable is None and dst_coll.get_array() is not None:
            first_mappable = dst_coll
    return first_mappable


def _mapped_transform(transform: object, src_ax: Axes, dst_ax: Axes, src_fig: Figure, dst_fig: Figure) -> object:
    if transform is src_ax.transData:
        return dst_ax.transData
    if transform is src_ax.transAxes:
        return dst_ax.transAxes
    if transform is src_fig.transFigure:
        return dst_fig.transFigure
    return transform


def _copy_texts(src_ax: Axes, dst_ax: Axes, src_fig: Figure, dst_fig: Figure) -> None:
    for src_text in src_ax.texts:
        x, y = src_text.get_position()
        transform = _mapped_transform(src_text.get_transform(), src_ax, dst_ax, src_fig, dst_fig)
        dst_text = dst_ax.text(x, y, src_text.get_text(), transform=transform)
        dst_text.update_from(src_text)
        dst_text.set_transform(transform)


def _copy_axes_style(src_ax: Axes, src_fig: Figure, dst_ax: Axes) -> None:
    dst_ax.set_xscale(src_ax.get_xscale())
    dst_ax.set_yscale(src_ax.get_yscale())
    dst_ax.set_xlim(src_ax.get_xlim())
    dst_ax.set_ylim(src_ax.get_ylim())
    dst_ax.set_xlabel(src_ax.get_xlabel())
    dst_ax.set_ylabel(src_ax.get_ylabel())
    dst_ax.set_title(src_ax.get_title())
    dst_ax.set_facecolor(src_ax.get_facecolor())
    dst_ax.set_aspect(src_ax.get_aspect())
    src_pos = src_ax.get_position()
    src_fig_w, src_fig_h = src_fig.get_size_inches()
    src_ax_w = src_pos.width * src_fig_w
    src_ax_h = src_pos.height * src_fig_h
    if src_ax_w > 0 and src_ax_h > 0:
        dst_ax.set_box_aspect(src_ax_h / src_ax_w)
    dst_ax.grid(src_ax.get_xgridlines()[0].get_visible() if src_ax.get_xgridlines() else False)


def _copy_plot_to_axis(
    src_ax: Axes,
    src_fig: Figure,
    dst_ax: Axes,
    dst_fig: Figure,
    title_override: str | None,
) -> PathCollection | None:
    _copy_lines(src_ax, dst_ax)
    mappable = _copy_path_collections(src_ax, dst_ax)
    _copy_texts(src_ax, dst_ax, src_fig, dst_fig)
    _copy_axes_style(src_ax, src_fig, dst_ax)
    if title_override is not None:
        dst_ax.set_title(title_override)
    return mappable


def _add_colorbar_if_present(
    src_fig: Figure,
    src_cbar_ax: Axes | None,
    dst_fig: Figure,
    dst_ax: Axes,
    mappable: PathCollection | None,
) -> None:
    if src_cbar_ax is None or mappable is None:
        return
    label = src_cbar_ax.get_ylabel()
    colorbar = dst_fig.colorbar(mappable, ax=dst_ax, fraction=0.046, pad=0.04)
    if label:
        colorbar.set_label(label)


def main() -> None:
    args = parse_args()
    paths = sorted(args.in_dir.glob(args.pattern))
    if not paths:
        raise SystemExit(f"No files found in {args.in_dir} matching {args.pattern}")
    non_pkl = [path for path in paths if path.suffix.lower() != ".pkl"]
    if non_pkl:
        preview = ", ".join(path.name for path in non_pkl[:5])
        extra = "" if len(non_pkl) <= 5 else f" (+{len(non_pkl) - 5} more)"
        raise SystemExit(
            f"This script is PKL-only. Found non-PKL files in selection: {preview}{extra}"
        )

    cols = max(1, args.cols)
    rows = math.ceil(len(paths) / cols)
    loaded: list[tuple[Path, Axes, Figure, Axes | None]] = []
    src_widths: list[float] = []
    src_heights: list[float] = []
    for path in paths:
        try:
            obj = _load_pickle_with_numpy_compat(path)
        except Exception as exc:
            raise SystemExit(f"Failed to read pickle file {path}: {exc}") from exc
        src_ax, src_fig = _extract_plot_axes(obj, path)
        src_cbar_ax = _find_colorbar_axis(src_fig)
        src_fig_w, src_fig_h = src_fig.get_size_inches()
        src_widths.append(float(src_fig_w))
        src_heights.append(float(src_fig_h))
        loaded.append((path, src_ax, src_fig, src_cbar_ax))

    cell_w = max(src_widths) if src_widths else 8.0
    cell_h = max(src_heights) if src_heights else 6.0
    fig_w = cell_w * cols
    fig_h = cell_h * rows
    fig, axes = plt.subplots(rows, cols, figsize=(fig_w, fig_h), constrained_layout=True)
    if rows == 1 and cols == 1:
        axes_list = [axes]
    elif rows == 1:
        axes_list = list(axes)
    else:
        axes_list = [ax for row_axes in axes for ax in row_axes]

    for ax in axes_list[len(paths):]:
        ax.axis("off")

    for dst_ax, (path, src_ax, src_fig, src_cbar_ax) in zip(axes_list, loaded):
        title_override = path.stem if args.show_names else None
        mappable = _copy_plot_to_axis(src_ax, src_fig, dst_ax, fig, title_override=title_override)
        _add_colorbar_if_present(src_fig, src_cbar_ax, fig, dst_ax, mappable)
        plt.close(src_fig)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    plt.close(fig)
    print(f"Wrote {args.out} ({len(paths)} pickles)")


if __name__ == "__main__":
    main()
