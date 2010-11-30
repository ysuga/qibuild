###
#
# Could one day contain stuff such as:
#
#   - Wrappers around SWIG
#
#   - Auto-generation of setup.py files
#
#   - Adding a "python setup.py install --prefix=CMAKE_INSTALL_PREFIX" command
#
#  ....


include(CMakeParseArguments)

#############
#
# Nice wrapper for swig.
#
# wrap_python(module_name interface_file SRCS srcs... DEPENDENCIES deps ...)
#
# /!\ The module_name must be the same as the one declare in ${interface_file}
# for instance, if module_name equals foo, foo.i must contain:
#   %module foo
##############
function(qi_swig_wrap_python module_name interface_file)
  cmake_parse_arguments(ARG "" "" "SRC;DEPENDS" ${ARGN})

  # Basic configurations
  find_package(SWIG REQUIRED)
  include(${SWIG_USE_FILE})
  set_source_files_properties(${interface_file} PROPERTIES CPLUSPLUS ON)
  # tell swig that the generated module name is ${module_name}.py
  # without this property, it assumes that it is ${interface_file}.py
  # TODO: check that it is a correct way to do this and not a nifty hack
  set_source_files_properties(
    ${interface_file} PROPERTIES SWIG_MODULE_NAME "${module_name}")


  # Everything will end up in ${SDK_DIR}/${SDK_DIR}, so that
  # setting PYTHONPATH and LD_LIBRARY_PATH (or PATH) is enough
  set(CMAKE_SWIG_OUTDIR ${QI_SDK_DIR}/${QI_SDK_LIB})

  ##
  # Deal with dependencies:
  foreach (_dep ${ARG_DEPENDS})
    find_package(${_dep})
    include_directories(${${_dep}_INCLUDE_DIR})
  endforeach()

  # Since there is often a "lazy" include in the interface file:
  include_directories(${CMAKE_CURRENT_SOURCE_DIR})

  swig_add_module(${module_name} python ${interface_file} ${ARG_SRC})

  ##
  # Deal with the newly created target

  # Store the target created by swig_add_module in a more friendly name:
  set(_swig_target ${SWIG_MODULE_${module_name}_REAL_NAME})

  qi_use_lib(${_swig_target} PYTHON ${_deps})

  set_target_properties(${_swig_target}
    PROPERTIES
      LIBRARY_OUTPUT_DIRECTORY "${QI_SDK_DIR}/${QI_SDK_LIB}"
  )

  # Be sure a .pyd file gets created, even though we
  # use an old version of swig, which may create .dll files ...
  if (WIN32)
    set_target_properties(${_swig_target} PROPERTIES SUFFIX   ".pyd"
                                             DEBUG_POSTFIX "_d")
    # Make sure _swig_target is put in the right place
    win32_copy_target(${_swig_target} "${QI_SDK_DIR}/${QI_SDK_LIB}")
  endif(WIN32)

  # Re-create install rules:
  install(TARGETS ${_swig_target}
    COMPONENT python
    LIBRARY DESTINATION "${QI_SDK_LIB}"
    RUNTIME DESTINATION "${QI_SDK_LIB}"
  )

  install(FILES "${QI_SDK_DIR}/${QI_SDK_LIB}/${module_name}.py"
    COMPONENT python
    DESTINATION "${QI_SDK_LIB}"
  )


endfunction()