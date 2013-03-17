from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

# -------------------------------------------------------------------
#   Hack distutils to stop being a muppet and throwing
#   -Qunused-arguments around. Needed to get gcc-4.7 working.
# -------------------------------------------------------------------
import distutils
import distutils.sysconfig
distutils.sysconfig.get_config_vars()
for key in distutils.sysconfig._config_vars:
    if key in ['CONFIG_ARGS', 'PY_CFLAGS', 'CFLAGS']:
        distutils.sysconfig._config_vars[key] = distutils.sysconfig._config_vars[key].replace("-Qunused-arguments ", "")
# -------------------------------------------------------------------

ext_modules = [Extension("process_line", ["process_line.pyx"])]

setup(
    name = "process_line",
    cmdclass = {"build_ext": build_ext},
    ext_modules = ext_modules
)

