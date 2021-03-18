cmake_minimum_required(VERSION 3.10)

# set the project name
project(Tradfri)

mark_as_advanced(CMAKE_INSTALL_PREFIX)

mark_as_advanced(CMAKE_BUILD_TYPE)

# External
# include(ExternalProject)
# set(EXTERNAL_INSTALL_LOCATION ${CMAKE_BINARY_DIR}/external)

find_program(Docker_EXECUTABLE docker)
if(NOT Docker_EXECUTABLE)
    message(FATAL_ERROR "Cannot find the docker executable!")
endif()

option(Use_Cache "Use cache" YES)
option(Push_to_Hub "Push images to dockerhub" YES)

option(Build_amd64 "Build for linux/amd64" YES)
option(Build_arm64 "Build for linux/arm64" YES)
option(Build_arm/v7 "Build for linux/arm7v7" YES)

IF(Build_amd64)
    list(APPEND platform "linux/amd64")
ENDIF(Build_amd64)

IF(Build_arm64)
    list(APPEND platform "linux/arm64")
ENDIF(Build_arm64)

IF (Build_arm/v7)
    list(APPEND platform "linux/arm/v7")
ENDIF(Build_arm/v7)

string (REPLACE ";" "," platform "${platform}")


message(STATUS "platform='${platform}'")

IF(Push_to_Hub)
    set(BUILD_TARGET --push)
ELSE(Push_to_Hub)
    set(BUILD_TARGET --load)
ENDIF(Push_to_Hub)

IF(Use_Cache)
    set(BUILD_CACHE "")
ELSE(Use_Cache)
    set(BUILD_CACHE "--no-cache")
ENDIF(Use_Cache)

set(Tradfri_Version "latest" CACHE STRING "Version tag to use")
set_property(CACHE Tradfri_Version PROPERTY STRINGS latest dev)

set(Domoticz_Version "stable" CACHE STRING "Version of Domoticz to use")
set_property(CACHE Domoticz_Version PROPERTY STRINGS stable beta)
 
set(Tradfricoap_Version "master" CACHE STRING "Branch of tradfricoap to use")
set_property(CACHE Tradfricoap_Version PROPERTY STRINGS master development)

set(Py3coap_Version "master" CACHE STRING "Branch of tradfricoap to use")
set_property(CACHE Py3coap_Version PROPERTY STRINGS master development)

execute_process(COMMAND python3 ../plugin.py version -s OUTPUT_VARIABLE Tradfri_Version_Number OUTPUT_STRIP_TRAILING_WHITESPACE)

IF(Tradfri_Version STREQUAL "dev")
    set(Tradfri_Version_Number "${Tradfri_Version_Number}-dev")
ENDIF()

message(STATUS "Tradfri version='${Tradfri_Version_Number}'")

message(STATUS "Build targed='${BUILD_TARGET}'")

IF(Domoticz_Version STREQUAL "stable")
    set(Domoticz_Channel release)
ELSEIF(Domoticz_Version STREQUAL "beta")
    set(Domoticz_Channel beta)
ENDIF()

add_custom_target(tradfri
    ALL
    COMMAND ${Docker_EXECUTABLE} buildx build ${BUILD_CACHE} ${BUILD_TARGET} --platform=${platform} --build-arg DOMOTICZ_VERSION=${Domoticz_Version} -t moroen/domoticz-tradfri:${Tradfri_Version_Number} -t moroen/domoticz-tradfri:${Tradfri_Version} -f Dockerfile ..    
)

add_custom_target(domoticz
    COMMAND ${Docker_EXECUTABLE} buildx build ${BUILD_CACHE} ${BUILD_TARGET} --platform=${platform} --build-arg DOMOTICZ_VERSION=${Domoticz_Channel} -t
    moroen/domoticz:${Domoticz_Version} -f Dockerfile.domoticz .
)

add_custom_target(build-tools
    COMMAND ${Docker_EXECUTABLE} run --privileged --rm tonistiigi/binfmt --install arm64,arm
)



