##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>
##
## Copyright (C) 2010 Aldebaran Robotics
##

include("${TOOLCHAIN_DIR}/cmake/libfind.cmake")

clean(LIRCCLIENT)

fpath(LIRCCLIENT lirc/lirc_client.h)
flib(LIRCCLIENT lirc_client)

export_lib(LIRCCLIENT)

