# Copyright (C) 2022  Nicolas Möser

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import os
import sys
from time import sleep

import keyboard
import numpy as np
import pandas
import pyautogui
import PySimpleGUI as sg
import importlib

from profiles import available_profiles
# from profiles.cold_war.menu import MENU_DICT
from profiles.general.buttons import *
from profiles.general.constants import *

DEBUG_MODE = False

pyautogui.PAUSE = 0.05

def set_height(current_height, target_height):
    if current_height == target_height:
        return
    elif current_height < target_height:
        n_diff = target_height - current_height
        for i in range(n_diff):
            if not DEBUG_MODE:
                keyboard.send('+')
                sleep(0.1)
    else:
        n_diff = current_height - target_height
        print(n_diff)
        for i in range(n_diff):
            if not DEBUG_MODE:
                keyboard.send('-')
                sleep(0.1)


def process_segment(grid, start_height):
    values = grid.z.sort_values().unique()
    min_height = grid[grid.z >= 0].z.min()
    
    if np.isnan(min_height):
        return start_height
    
    set_height(start_height, min_height)
    height = min_height

    for val in values:
        grid_extract = grid[grid.z == val]

        set_height(height, val)

        for ridx, row in grid_extract.iterrows():
            idx0 = row.x
            idx1 = row.y
            x_pos = int(idx0 * SQUARE_SIZE_X + UPPER_LEFT_SQUARE.x)
            y_pos = int(LOWER_RIGHT_SQUARE.y - idx1 * SQUARE_SIZE_Y)
            height = val

            if not DEBUG_MODE:
                pyautogui.click(x=x_pos, y=y_pos)

    return height

def set_n_squares(start_n_x, start_n_y, n_x, n_y, mode='window'):
    n_clicks_x = abs(int((start_n_x - n_x) / 2))
    n_clicks_y = abs(int((start_n_y - n_y) / 2))

    for i in range(n_clicks_x):
        if not DEBUG_MODE:
            if n_x <= start_n_x:
                if mode in ('window', 'finish'):
                    pyautogui.click(POS_HORIZONTAL_PLUS2, interval=0.05)
                if mode in ('window', 'init'):
                    pyautogui.click(POS_HORIZONTAL_MINUS, interval=0.05)
            else:
                if mode in ('window', 'init'):
                    pyautogui.click(POS_HORIZONTAL_PLUS, interval=0.05)
                if mode in ('window', 'finish'):
                    pyautogui.click(POS_HORIZONTAL_MINUS2, interval=0.05)    
    
    for i in range(n_clicks_y):
        if not DEBUG_MODE:
            if n_y <= start_n_y:
                if mode in ('window', 'finish'):
                    pyautogui.click(POS_VERTICAL_PLUS2, interval=0.05)    
                if mode in ('window', 'init'):
                    pyautogui.click(POS_VERTICAL_MINUS, interval=0.05)
            else:
                if mode in ('window', 'init'):
                    pyautogui.click(POS_VERTICAL_PLUS, interval=0.05)
                if mode in ('window', 'finish'):
                    pyautogui.click(POS_VERTICAL_MINUS2, interval=0.05)    

def display_gui():
    # Construct window layout
    layout = [
        [sg.Titlebar('CMAutoEditor')],
        [sg.Text('Profile: '), sg.Combo(values=list(available_profiles.keys()), default_value=list(available_profiles.keys())[0], 
                                        key='cm_profile')],
        [sg.Text('You are about to start CMAutoEditor.')],
        [sg.Text('If you haven\'t done so yet, open up the CM Scenario Editor.')], 
        [sg.Text('If you want to set elevations, go to map->Elevation and click \'Direct\'.')],
        [sg.Text('For OSM data, just go to \'map\' and stay on the first menu page (\'Ground 1\', etc).')],
        [sg.Text('Make sure the map size is 320m x 320m or check \'Take start size from file\' (only when continueing a map!).')],
        [sg.Text('Once you are ready to start click, \'Start CMAutoEditor\'.')], 
        [sg.Text('During the countdown switch back to the CM Scenario Editor.')],
        [sg.Text('In case something goes wrong, move the mouse cursor to one of the screen corners.')],
        [sg.Text('')],
        [sg.Text('Select file: ')], 
        [sg.Input(), sg.FileBrowse(key='filepath', file_types=(('CSV files', '*.csv'),))],
        [sg.Text('Countdown: '), sg.InputCombo(key='countdown',values=[5, 10, 15, 20, 25, 30], default_value=10)],
        [sg.Checkbox('Take start size from file (only for continueing a map!)', key='start_size_from_file', enable_events=True, default=False)],
        [sg.Text('Min. time between clicks [s]: '), sg.InputCombo(key='min_time',values=[0.05, 0.1, 0.15, 0.2], default_value=0.05), sg.Text(' Only increase if CMAutoEditor skips items.')],
        [sg.Text(text='', key='error_text')],
        [sg.Push(), sg.Button('Start CMAutoEditor', key='start'), sg.Exit(), sg.Push()]]

    # Create window with layout
    window = sg.Window('CMAutoEditor', layout)
    
    # Loop until window needs closing
    start = False
    while True:
        # Read UI inputs
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        
        if event == 'start':
            if values['filepath'] == '' or values['filepath'] is None:
                window['error_text'].update('Select a file before starting')
            else:
                start = True
                break

    window.close()
    # Start editor with UI inputs
    if start and values['filepath'] != '' and values['filepath'] != None:
        start_editor(values['filepath'], values['countdown'], values['start_size_from_file'], values['min_time'], available_profiles[values['cm_profile']])
            

def set_ground(df, map_df):
    for group_info, group in df.groupby(by=['menu', 'cat1', 'cat2', 'direction']):
        if group_info[0] not in MENU_DICT:
            continue

        if group_info[0] not in MENU_DICT or group_info[1] not in MENU_DICT:
            continue
        if not DEBUG_MODE:
            pyautogui.click(MENU_DICT[group_info[0]])
            pyautogui.click(MENU_DICT[group_info[1]])

        if group_info[2] in MENU_DICT:
            if not DEBUG_MODE:
                pyautogui.click(MENU_DICT[group_info[2]])
        if group_info[3] in MENU_DICT:
            if not DEBUG_MODE:
                pyautogui.click(MENU_DICT[group_info[3]])

        if group_info[0].startswith('Ground') or group_info[0].startswith('Brush'): 
            xmin, ymin = group.loc[:,['x','y']].min()
            xmax, ymax = group.loc[:,['x','y']].max()

            xy_mat = np.full((xmax-xmin+1, ymax-ymin+1), -1, dtype=int)
            
            for _, row in group.iterrows():
                xy_mat[row.x - xmin, row.y - ymin] = row.name

            group1 = pandas.DataFrame(columns=group.columns)
            group3 = pandas.DataFrame(columns=group.columns)
            group7 = pandas.DataFrame(columns=group.columns)
            group15 = pandas.DataFrame(columns=group.columns)

            brush_idx_lists = [[], [], [], []]

            for step, brush_idx_list in ((15, brush_idx_lists[1]), (7, brush_idx_lists[2]), (3, brush_idx_lists[3])):
                for x in range(step-1, xy_mat.shape[0]):
                    for y in range(step-1, xy_mat.shape[1]):
                        if not (xy_mat[x-step+1:x+1, y-step+1:y+1] < 0).any():
                            brush_indices = xy_mat[x-step+1+int(step/2), y-step+1+int(step/2)]
                            brush_idx_list.append(brush_indices)

                            xy_mat[x-step+1:x+1, y-step+1:y+1] = -1

            brush_idx_lists[0].extend(xy_mat[xy_mat >= 0])

            group1 = group[group.index.isin(brush_idx_lists[0])]
            group3 = group[group.index.isin(brush_idx_lists[3])]
            group7 = group[group.index.isin(brush_idx_lists[2])]
            group15 = group[group.index.isin(brush_idx_lists[1])]

            brush_groups = []
            for brush_group in [(BRUSH_1, group1), (BRUSH_3, group3), (BRUSH_7, group7), (BRUSH_15, group15)]:
                if len(brush_group[1]) > 0:
                    brush_groups.append(brush_group)

            
        else:
            brush_groups = [(BRUSH_1, group)]

        for brush_button, brush_group in brush_groups:
            if not DEBUG_MODE:
                pyautogui.click(brush_button)
            for row_idx, row in brush_group.iterrows():
                x_pos = int(row.x * SQUARE_SIZE_X + UPPER_LEFT_SQUARE.x)
                y_pos = int(LOWER_RIGHT_SQUARE.y - row.y * SQUARE_SIZE_Y)
                if not DEBUG_MODE:
                    pyautogui.click(x=x_pos, y=y_pos)

            map_df.loc[row_idx, 'done'] = 1

    
def start_editor(filepath, countdown, start_size_from_file=False, min_time=0.05, profile='cold_war'):
    global MENU_DICT
    MENU_DICT = importlib.import_module('profiles.{}.menu'.format(profile)).MENU_DICT
    pyautogui.PAUSE = min_time
    map_df = pandas.read_csv(filepath)
    map_df.z = map_df.z.round().astype(int)

    if 'done' not in map_df:
        map_df['done'] = 0

    start_i_page_x = 0
    start_i_page_y = 0
    if start_size_from_file:
        prev_n_x = np.floor(map_df.x.max()).astype(int) + PAGE_RIGHT_MARGIN
        prev_n_y = np.floor(map_df.y.max()).astype(int) + PAGE_BOTTOM_MARGIN
    else:
        prev_n_x = START_N_SQUARES_X
        prev_n_y = START_N_SQUARES_Y

    try:    
        map_df = map_df[map_df['done'] == 0]
        total_n_squares_x = int(map_df.x.max()) + 1
        total_n_squares_y = int(map_df.y.max()) + 1

        n_pages_x, n_x_remain = np.divmod(total_n_squares_x, PAGE_N_SQUARES_X - PAGE_RIGHT_MARGIN, dtype=int)
        n_pages_y, n_y_remain = np.divmod(total_n_squares_y, PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN - PAGE_BOTTOM_MARGIN, dtype=int)
        n_x_remain = (np.floor(n_x_remain / 2) * 2).astype(int)
        n_y_remain = (np.floor(n_y_remain / 2) * 2).astype(int)

        map_df = map_df[(map_df.x >= 0) & (map_df.y >= 0) & (map_df.x < (n_pages_x * PAGE_N_SQUARES_X + n_x_remain)) & (map_df.y < (n_pages_y * PAGE_N_SQUARES_Y + n_y_remain))]
                        
        total_n_squares_x = n_pages_x * (PAGE_N_SQUARES_X - PAGE_RIGHT_MARGIN) + n_x_remain
        total_n_squares_y = n_pages_y * (PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN - PAGE_BOTTOM_MARGIN) + n_y_remain

        height = START_HEIGHT

        if not DEBUG_MODE:
            pyautogui.countdown(countdown)

        for i_page_y in range(n_pages_y + 1):
            for i_page_x in range(n_pages_x + 1):
                if i_page_x < n_pages_x:
                    n_squares_x = (i_page_x + 1) * PAGE_N_SQUARES_X - i_page_x * PAGE_RIGHT_MARGIN
                    xmax = total_n_squares_x - i_page_x * (PAGE_N_SQUARES_X - PAGE_RIGHT_MARGIN)
                    xmin = xmax - (PAGE_N_SQUARES_X - PAGE_RIGHT_MARGIN)
                    origin_x = total_n_squares_x - (i_page_x + 1) * (PAGE_N_SQUARES_X - PAGE_RIGHT_MARGIN)
                else:
                    n_squares_x = i_page_x * PAGE_N_SQUARES_X - (i_page_x - 1) * PAGE_RIGHT_MARGIN + n_x_remain #  ?
                    xmax = n_x_remain
                    xmin = 0
                    origin_x = 0
                if i_page_y < n_pages_y:
                    n_squares_y = (i_page_y + 1) * PAGE_N_SQUARES_Y - i_page_y * (PAGE_TOP_MARGIN + PAGE_BOTTOM_MARGIN)
                    ymax = (i_page_y + 1) * (PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN - PAGE_BOTTOM_MARGIN)
                    ymin = ymax - (PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN - PAGE_BOTTOM_MARGIN)
                    origin_y = i_page_y * (PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN) - (i_page_y + 1) * PAGE_BOTTOM_MARGIN
                else:
                    n_squares_y = i_page_y * PAGE_N_SQUARES_Y - (i_page_y - 1) * (PAGE_TOP_MARGIN + PAGE_BOTTOM_MARGIN) + n_y_remain
                    ymax = total_n_squares_y
                    ymin = total_n_squares_y - n_y_remain
                    origin_y = total_n_squares_y - (PAGE_N_SQUARES_Y - PAGE_TOP_MARGIN)

                if xmax == xmin or ymax == ymin:
                    continue

                if (prev_n_x == START_N_SQUARES_X and prev_n_y == START_N_SQUARES_Y) or start_size_from_file:
                    mode = 'init'
                else:
                    mode = 'window'
                set_n_squares(prev_n_x, prev_n_y, n_squares_x, n_squares_y, mode)
                if start_size_from_file:
                    set_n_squares(n_squares_x, n_squares_y, n_squares_x - 2, n_squares_y - 2, 'window')
                    start_size_from_file = False

                prev_n_x = n_squares_x
                prev_n_y = n_squares_y

                sub_df = map_df[map_df.x.between(xmin, xmax, inclusive='left') & map_df.y.between(ymin, ymax, inclusive='left')].copy(deep=True)
                sub_df.x = sub_df.x - origin_x
                sub_df.y = sub_df.y - origin_y
                height = process_segment(sub_df, height)
                if 'menu' in map_df.columns:
                    set_ground(sub_df, map_df)

        set_n_squares(total_n_squares_x, total_n_squares_y, PAGE_N_SQUARES_X, PAGE_N_SQUARES_Y, 'finish')
        set_n_squares(total_n_squares_x, total_n_squares_y, total_n_squares_x, total_n_squares_y - PAGE_TOP_MARGIN, 'window')

    except pyautogui.FailSafeException:
        pass
        # map_df.to_csv(args.input + '.checkpoint')
        # meta_df = pandas.DataFrame({'prev_n_x': [prev_n_x], 'prev_n_y': [prev_n_y], 'start_i_page_x': [i_page_x], 'start_i_page_y': [i_page_y]})
        # meta_df.to_csv(args.input + '.meta.checkpoint')

    pyautogui.alert(text='CMAutoEditor has finished processing the input data.', title='CMAutoEditor')
        
if __name__ == '__main__':
    sg.theme('Dark')
    sg.theme_button_color('#002366')

    #Run the gui if no arguments are inputted
    if len(sys.argv) == 1:
        display_gui()
    else:
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument('-i', '--input', required=True, help='File containing input data in csv-Format. Data is coded in x, y and z columns.')
        arg_parser.add_argument('-c', '--countdown', required=False, type=int, help='Countdown until CMAutoEditor starts clicking in CM.', default=5)
        arg_parser.add_argument('--start-size-from-file', required=False, action='store_true', help='If true take starting map size from file. Useful when continueing map creation.', default=False)
        arg_parser.add_argument('-p', '--profile', required=False, default='cold_war', type=str)
        arg_parser.add_argument('-t', '--min-time', required=False, default=0.05, type=float)
        args = arg_parser.parse_args()
    
        return_val = sg.popup_ok_cancel('CMAutoEditor is about to run on {}.'.format(args.input),
        'If you haven\'t done so yet, open up the CM Scenario Editor, go to map->Elevation and click \'Direct\'. Make sure the size is 320m x 320m.',
        'Once you are ready to start click \'Ok\'. You will then have {}s to switch back to the CM Scenario Editor.'.format(args.countdown),
        'In case something goes wrong, move the mouse cursor to one of the screen corners. This will stop CMAutoEditor.', 
        title='CMAutoEditor')
        
        if return_val == 'Cancel' or return_val is None:
            exit()
        
        start_editor(args.input, args.countdown, args.start_size_from_file, args.min_time, args.profile)
