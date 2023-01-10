SET(TVM_OUT_DIR ${CONFIG_MLONMCU_CODEGEN_DIR}/codegen/host/)
SET(EXTRA_SRC ml_interface_tvm.c)

FILE(GLOB TVM_SRCS ${TVM_OUT_DIR}/src/*_lib*.c ${TVM_OUT_DIR}/src/*_lib*.cc)

# IF(NOT TVM_SRCS)
#     MESSAGE(STATUS "NO SOURCES")
#     FILE(GLOB TVM_OBJS ${TVM_OUT_DIR}/lib/*_lib*.o)
#     MESSAGE(STATUS "TVM_OBJS=${TVM_OBJS}")
#     # ADD_LIBRARY(tvm_extension OBJECT IMPORTED)
#
#     # SET_PROPERTY(TARGET tvm_extension PROPERTY
#     #     IMPORTED_OBJECTS ${TVM_OBJS}
#     # )
# ELSE()
#     # Need this in extra target to avoid circular dependency .
#     # ADD_LIBRARY(tvm_extension STATIC ${TVM_SRCS})
#     TARGET_INCLUDE_DIRECTORIES(tvm_extension PUBLIC ${TVM_HEADERS} ${TVM_OUT_DIR}/include ${CONFIG_MLONMCU_CODEGEN_DIR})
#     TARGET_LINK_LIBRARIES(tvm_extension PUBLIC m)
#     TARGET_LINK_LIBRARIES(tvm_extension PUBLIC ${TVM_LIB})
# ENDIF()
#
# SET(EXTRA_SRC ${EXTRA_SRC} ${CONFIG_MLONMCU_CODEGEN_DIR}/${TVM_WRAPPER_FILENAME})
# TARGET_LINK_LIBRARIES(${TVM_LIB} PUBLIC tvm_extension)
# SET(EXTRA_INC ${TVM_OUT_DIR}/include ${CONFIG_MLONMCU_CODEGEN_DIR})
#
# SET(EXTRA_LIBS tvm_extension ${TVM_LIB})
#
# FOREACH(ENTRY ${CONFIG_TVM_EXTRA_LIBS})
#     TARGET_LINK_LIBRARIES(tvm_extension PUBLIC ${ENTRY})
# ENDFOREACH()
# FOREACH(ENTRY ${CONFIG_TVM_EXTRA_INCS})
#     TARGET_INCLUDE_DIRECTORIES(tvm_extension PUBLIC ${ENTRY})
# ENDFOREACH()
# FOREACH(ENTRY ${CONFIG_TVM_EXTRA_DEPS})
#     ADD_DEPENDENCIES(tvm_extension ${ENTRY})
# ENDFOREACH()