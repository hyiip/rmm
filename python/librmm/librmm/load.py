# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: Apache-2.0
#

import ctypes
import os
import sys

# Loading with RTLD_LOCAL adds the library itself to the loader's
# loaded library cache without loading any symbols into the global
# namespace. This allows libraries that express a dependency on
# this library to be loaded later and successfully satisfy this dependency
# without polluting the global symbol table with symbols from
# librmm that could conflict with symbols from other DSOs.
PREFERRED_LOAD_FLAG = ctypes.RTLD_LOCAL


def _load_system_installation(soname: str):
    """Try to dlopen() the library indicated by ``soname``
    Raises ``OSError`` if library cannot be loaded.
    """
    return ctypes.CDLL(soname, PREFERRED_LOAD_FLAG)


def _load_wheel_installation(soname: str):
    """Try to dlopen() the library indicated by ``soname``

    Returns ``None`` if the library cannot be loaded.
    """
    libdir = "bin" if sys.platform == "win32" else "lib64"
    if os.path.isfile(
        lib := os.path.join(os.path.dirname(__file__), libdir, soname)
    ):
        return ctypes.CDLL(lib, PREFERRED_LOAD_FLAG)
    return None


def _add_dll_directories():
    """On Windows, add DLL directories so .pyd files can find native libraries."""
    if sys.platform != "win32":
        return
    pkg_dir = os.path.dirname(__file__)
    for subdir in ("bin", "lib"):
        dll_dir = os.path.join(pkg_dir, subdir)
        if os.path.isdir(dll_dir):
            os.add_dll_directory(dll_dir)


def load_library():
    """Dynamically load librmm.so and its dependencies"""
    try:
        # rapids-logger must be loaded before librmm because librmm references
        # it.
        import rapids_logger

        rapids_logger.load_library()
    except ModuleNotFoundError:
        # librmm's runtime dependency on rapids-logger may be satisfied by a
        # natively installed library or a conda package, in which case the
        # import will fail and we assume the library is discoverable on system
        # paths.
        pass

    # On Windows, register DLL directories so that extension modules (.pyd)
    # can resolve their native library dependencies (rmm.dll, etc.).
    _add_dll_directories()

    prefer_system_installation = (
        os.getenv("RAPIDS_LIBRMM_PREFER_SYSTEM_LIBRARY", "false").lower()
        != "false"
    )

    soname = "rmm.dll" if sys.platform == "win32" else "librmm.so"
    librmm_lib = None
    if prefer_system_installation:
        # Prefer a system library if one is present to
        # avoid clobbering symbols that other packages might expect, but if no
        # other library is present use the one in the wheel.
        try:
            librmm_lib = _load_system_installation(soname)
        except OSError:
            librmm_lib = _load_wheel_installation(soname)
    else:
        # Prefer the libraries bundled in this package. If they aren't found
        # (which might be the case in builds where the library was prebuilt before
        # packaging the wheel), look for a system installation.
        try:
            librmm_lib = _load_wheel_installation(soname)
            if librmm_lib is None:
                librmm_lib = _load_system_installation(soname)
        except OSError:
            # If none of the searches above succeed, just silently return None
            # and rely on other mechanisms (like RPATHs on other DSOs) to
            # help the loader find the library.
            pass

    # The caller almost never needs to do anything with this library, but no
    # harm in offering the option since this object at least provides a handle
    # to inspect where librmm was loaded from.
    return librmm_lib
