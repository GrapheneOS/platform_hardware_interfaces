#!/usr/bin/python3

# Copyright (C) 2022 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""A script to generate Java files and CPP header files based on annotations in VehicleProperty.aidl

   Need ANDROID_BUILD_TOP environmental variable to be set. This script will update
   ChangeModeForVehicleProperty.h and AccessForVehicleProperty.h under generated_lib/cpp and
   ChangeModeForVehicleProperty.java, AccessForVehicleProperty.java, EnumForVehicleProperty.java under generated_lib/java.

   Usage:
   $ python generate_annotation_enums.py
"""
import argparse
import filecmp
import os
import re
import sys
import tempfile

PROP_AIDL_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/' +
    'automotive/vehicle/VehicleProperty.aidl')
CHANGE_MODE_CPP_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl/generated_lib/cpp/' +
    'ChangeModeForVehicleProperty.h')
ACCESS_CPP_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl/generated_lib/cpp/' +
    'AccessForVehicleProperty.h')
CHANGE_MODE_JAVA_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl/generated_lib/java/' +
    'ChangeModeForVehicleProperty.java')
ACCESS_JAVA_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl/generated_lib/java/' +
    'AccessForVehicleProperty.java')
ENUM_JAVA_FILE_PATH = ('hardware/interfaces/automotive/vehicle/aidl/generated_lib/java/' +
                         'EnumForVehicleProperty.java')
SCRIPT_PATH = 'hardware/interfaces/automotive/vehicle/tools/generate_annotation_enums.py'

TAB = '    '
RE_ENUM_START = re.compile('\s*enum VehicleProperty \{')
RE_ENUM_END = re.compile('\s*\}\;')
RE_COMMENT_BEGIN = re.compile('\s*\/\*\*?')
RE_COMMENT_END = re.compile('\s*\*\/')
RE_CHANGE_MODE = re.compile('\s*\* @change_mode (\S+)\s*')
RE_ACCESS = re.compile('\s*\* @access (\S+)\s*')
RE_DATA_ENUM = re.compile('\s*\* @data_enum (\S+)\s*')
RE_UNIT = re.compile('\s*\* @unit (\S+)\s+')
RE_VALUE = re.compile('\s*(\w+)\s*=(.*)')

LICENSE = """/*
 * Copyright (C) 2023 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * DO NOT EDIT MANUALLY!!!
 *
 * Generated by tools/generate_annotation_enums.py.
 */

// clang-format off

"""

CHANGE_MODE_CPP_HEADER = """#ifndef android_hardware_automotive_vehicle_aidl_generated_lib_ChangeModeForVehicleProperty_H_
#define android_hardware_automotive_vehicle_aidl_generated_lib_ChangeModeForVehicleProperty_H_

#include <aidl/android/hardware/automotive/vehicle/VehicleProperty.h>
#include <aidl/android/hardware/automotive/vehicle/VehiclePropertyChangeMode.h>

#include <unordered_map>

namespace aidl {
namespace android {
namespace hardware {
namespace automotive {
namespace vehicle {

std::unordered_map<VehicleProperty, VehiclePropertyChangeMode> ChangeModeForVehicleProperty = {
"""

CHANGE_MODE_CPP_FOOTER = """
};

}  // namespace vehicle
}  // namespace automotive
}  // namespace hardware
}  // namespace android
}  // aidl

#endif  // android_hardware_automotive_vehicle_aidl_generated_lib_ChangeModeForVehicleProperty_H_
"""

ACCESS_CPP_HEADER = """#ifndef android_hardware_automotive_vehicle_aidl_generated_lib_AccessForVehicleProperty_H_
#define android_hardware_automotive_vehicle_aidl_generated_lib_AccessForVehicleProperty_H_

#include <aidl/android/hardware/automotive/vehicle/VehicleProperty.h>
#include <aidl/android/hardware/automotive/vehicle/VehiclePropertyAccess.h>

#include <unordered_map>

namespace aidl {
namespace android {
namespace hardware {
namespace automotive {
namespace vehicle {

std::unordered_map<VehicleProperty, VehiclePropertyAccess> AccessForVehicleProperty = {
"""

ACCESS_CPP_FOOTER = """
};

}  // namespace vehicle
}  // namespace automotive
}  // namespace hardware
}  // namespace android
}  // aidl

#endif  // android_hardware_automotive_vehicle_aidl_generated_lib_AccessForVehicleProperty_H_
"""

CHANGE_MODE_JAVA_HEADER = """package android.hardware.automotive.vehicle;

import java.util.Map;

public final class ChangeModeForVehicleProperty {

    public static final Map<Integer, Integer> values = Map.ofEntries(
"""

CHANGE_MODE_JAVA_FOOTER = """
    );

}
"""

ACCESS_JAVA_HEADER = """package android.hardware.automotive.vehicle;

import java.util.Map;

public final class AccessForVehicleProperty {

    public static final Map<Integer, Integer> values = Map.ofEntries(
"""

ACCESS_JAVA_FOOTER = """
    );

}
"""

ENUM_JAVA_HEADER = """package android.hardware.automotive.vehicle;

import java.util.List;
import java.util.Map;

public final class EnumForVehicleProperty {

    public static final Map<Integer, List<Class<?>>> values = Map.ofEntries(
"""

ENUM_JAVA_FOOTER = """
    );

}
"""


class PropertyConfig:
    """Represents one VHAL property definition in VehicleProperty.aidl."""

    def __init__(self):
        self.name = None
        self.description = None
        self.change_mode = None
        self.access_modes = []
        self.enum_types = []
        self.unit_type = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ('PropertyConfig{{' +
            'name: {}, description: {}, change_mode: {}, access_modes: {}, enum_types: {}' +
            ', unit_type: {}}}').format(self.name, self.description, self.change_mode,
                self.access_modes, self.enum_types, self.unit_type)


class FileParser:

    def __init__(self):
        self.configs = None

    def parseFile(self, input_file):
        """Parses the input VehicleProperty.aidl file into a list of property configs."""
        processing = False
        in_comment = False
        configs = []
        config = None
        with open(input_file, 'r') as f:
            for line in f.readlines():
                if RE_ENUM_START.match(line):
                    processing = True
                elif RE_ENUM_END.match(line):
                    processing = False
                if not processing:
                    continue
                if RE_COMMENT_BEGIN.match(line):
                    in_comment = True
                    config = PropertyConfig()
                    description = ''
                if RE_COMMENT_END.match(line):
                    in_comment = False
                if in_comment:
                    if not config.description:
                        sline = line.strip()
                        # Skip the first line of comment
                        if sline.startswith('*'):
                            # Remove the '*'.
                            sline = sline[1:].strip()
                            # We reach an empty line of comment, the description part is ending.
                            if sline == '':
                                config.description = description
                            else:
                                if description != '':
                                    description += ' '
                                description += sline
                    match = RE_CHANGE_MODE.match(line)
                    if match:
                        config.change_mode = match.group(1).replace('VehiclePropertyChangeMode.', '')
                    match = RE_ACCESS.match(line)
                    if match:
                        config.access_modes.append(match.group(1).replace('VehiclePropertyAccess.', ''))
                    match = RE_UNIT.match(line)
                    if match:
                        config.unit_type = match.group(1)
                    match = RE_DATA_ENUM.match(line)
                    if match:
                        config.enum_types.append(match.group(1))
                else:
                    match = RE_VALUE.match(line)
                    if match:
                        prop_name = match.group(1)
                        if prop_name == 'INVALID':
                            continue
                        if not config.change_mode:
                            raise Exception(
                                    'No change_mode annotation for property: ' + prop_name)
                        if not config.access_modes:
                            raise Exception(
                                    'No access_mode annotation for property: ' + prop_name)
                        config.name = prop_name
                        configs.append(config)

        self.configs = configs

    def convert(self, output, header, footer, cpp, field):
        """Converts the property config file to C++/Java output file."""
        counter = 0
        content = LICENSE + header
        for config in self.configs:
            if field == 'change_mode':
                if cpp:
                    annotation = "VehiclePropertyChangeMode::" + config.change_mode
                else:
                    annotation = "VehiclePropertyChangeMode." + config.change_mode
            elif field == 'access_mode':
                if cpp:
                    annotation = "VehiclePropertyAccess::" + config.access_modes[0]
                else:
                    annotation = "VehiclePropertyAccess." + config.access_modes[0]
            elif field == 'enum_types':
                if len(config.enum_types) < 1:
                    continue;
                if not cpp:
                    annotation = "List.of(" + ', '.join([class_name + ".class" for class_name in config.enum_types]) + ")"
            else:
                raise Exception('Unknown field: ' + field)
            if counter != 0:
                content += '\n'
            if cpp:
                content += (TAB + TAB + '{VehicleProperty::' + config.name + ', ' +
                            annotation + '},')
            else:
                content += (TAB + TAB + 'Map.entry(VehicleProperty.' + config.name + ', ' +
                            annotation + '),')
            counter += 1

        # Remove the additional ',' at the end for the Java file.
        if not cpp:
            content = content[:-1]

        content += footer

        with open(output, 'w') as f:
            f.write(content)

    def outputAsCsv(self, output):
        content = 'name,description,change mode,access mode,enum type,unit type\n'
        for config in self.configs:
            enum_types = None
            if not config.enum_types:
                enum_types = '/'
            else:
                enum_types = '/'.join(config.enum_types)
            unit_type = config.unit_type
            if not unit_type:
                unit_type = '/'
            access_modes = ''
            content += '"{}","{}","{}","{}","{}","{}"\n'.format(
                    config.name,
                    # Need to escape quote as double quote.
                    config.description.replace('"', '""'),
                    config.change_mode,
                    '/'.join(config.access_modes),
                    enum_types,
                    unit_type)

        with open(output, 'w+') as f:
            f.write(content)


def createTempFile():
    f = tempfile.NamedTemporaryFile(delete=False);
    f.close();
    return f.name


def main():
    parser = argparse.ArgumentParser(
            description='Generate Java and C++ enums based on annotations in VehicleProperty.aidl')
    parser.add_argument('--android_build_top', required=False, help='Path to ANDROID_BUILD_TOP')
    parser.add_argument('--preupload_files', nargs='*', required=False, help='modified files')
    parser.add_argument('--check_only', required=False, action='store_true',
            help='only check whether the generated files need update')
    parser.add_argument('--output_csv', required=False,
            help='Path to the parsing result in CSV style, useful for doc generation')
    args = parser.parse_args();
    android_top = None
    output_folder = None
    if args.android_build_top:
        android_top = args.android_build_top
        vehiclePropertyUpdated = False
        for preuload_file in args.preupload_files:
            if preuload_file.endswith('VehicleProperty.aidl'):
                vehiclePropertyUpdated = True
                break
        if not vehiclePropertyUpdated:
            return
    else:
        android_top = os.environ['ANDROID_BUILD_TOP']
    if not android_top:
        print('ANDROID_BUILD_TOP is not in environmental variable, please run source and lunch ' +
            'at the android root')

    aidl_file = os.path.join(android_top, PROP_AIDL_FILE_PATH)
    f = FileParser();
    f.parseFile(aidl_file)

    if args.output_csv:
        f.outputAsCsv(args.output_csv)
        return

    change_mode_cpp_file = os.path.join(android_top, CHANGE_MODE_CPP_FILE_PATH);
    access_cpp_file = os.path.join(android_top, ACCESS_CPP_FILE_PATH);
    change_mode_java_file = os.path.join(android_top, CHANGE_MODE_JAVA_FILE_PATH);
    access_java_file = os.path.join(android_top, ACCESS_JAVA_FILE_PATH);
    enum_java_file = os.path.join(android_top, ENUM_JAVA_FILE_PATH);
    temp_files = []

    if not args.check_only:
        change_mode_cpp_output = change_mode_cpp_file
        access_cpp_output = access_cpp_file
        change_mode_java_output = change_mode_java_file
        access_java_output = access_java_file
        enum_java_output = enum_java_file
    else:
        change_mode_cpp_output = createTempFile()
        temp_files.append(change_mode_cpp_output)
        access_cpp_output = createTempFile()
        temp_files.append(access_cpp_output)
        change_mode_java_output = createTempFile()
        temp_files.append(change_mode_java_output)
        access_java_output = createTempFile()
        temp_files.append(access_java_output)
        enum_java_output = createTempFile()
        temp_files.append(enum_java_output)

    try:
        f.convert(change_mode_cpp_output, CHANGE_MODE_CPP_HEADER, CHANGE_MODE_CPP_FOOTER,
                True, 'change_mode')
        f.convert(change_mode_java_output, CHANGE_MODE_JAVA_HEADER,
                CHANGE_MODE_JAVA_FOOTER, False, 'change_mode')
        f.convert(access_cpp_output, ACCESS_CPP_HEADER, ACCESS_CPP_FOOTER, True, 'access_mode')
        f.convert(access_java_output, ACCESS_JAVA_HEADER, ACCESS_JAVA_FOOTER, False, 'access_mode')
        f.convert(enum_java_output, ENUM_JAVA_HEADER, ENUM_JAVA_FOOTER, False, 'enum_types')

        if not args.check_only:
            return

        if ((not filecmp.cmp(change_mode_cpp_output, change_mode_cpp_file)) or
                (not filecmp.cmp(change_mode_java_output, change_mode_java_file)) or
                (not filecmp.cmp(access_cpp_output, access_cpp_file)) or
                (not filecmp.cmp(access_java_output, access_java_file)) or
                (not filecmp.cmp(enum_java_output, enum_java_file))):
            print('The generated enum files for VehicleProperty.aidl requires update, ')
            print('Run \npython ' + android_top + '/' + SCRIPT_PATH)
            sys.exit(1)
    except Exception as e:
        print('Error parsing VehicleProperty.aidl')
        print(e)
        sys.exit(1)
    finally:
        for file in temp_files:
            os.remove(file)


if __name__ == '__main__':
    main()