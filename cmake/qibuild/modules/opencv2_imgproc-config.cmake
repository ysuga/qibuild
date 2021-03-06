## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

clean(OPENCV2_IMGPROC)
fpath(OPENCV2_IMGPROC opencv2/imgproc/imgproc.hpp)
flib(OPENCV2_IMGPROC OPTIMIZED NAMES opencv_imgproc)
flib(OPENCV2_IMGPROC DEBUG     NAMES opencv_imgproc)
qi_set_global(OPENCV2_IMGPROC_DEPENDS "OPENCV2_CORE")
export_lib(OPENCV2_IMGPROC)
