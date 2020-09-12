import argparse
import os
import codecs
from openpyxl import Workbook

####################
##### Files Management code
def extract_data_from_file(file_path):
  data_lines = []
  data_start_line = 'ZONE: DATA'
  collect_data = False

  with codecs.open(file_path, encoding='utf-8') as f:
    for line in f:
      line = line.strip()
      if collect_data:
        if line == '':
          break
        data_lines.append(line)

      if line == data_start_line:
        collect_data = True

  return data_lines

def data_lines_to_vectors(data_lines):
  x  = []
  y1 = []
  y2 = []

  for line in data_lines:
    cols = line.split()
    
    x.append(float(cols[0]))
    y1.append(float(cols[1]))
    y2.append(float(cols[4]))

  return x, y1, y2

def get_txp_from_file_name(file_name):
  x = file_name.split('______')[-1]
  return x.split('_')[0]

# def save_excel(filename, sheetname, satellite_name, x, obo_prev, fgm_output_power_prev):
def save_excel(filename, sheetname, data):
  wb = Workbook()
  # grab the active worksheet
  ws = wb.active
  ws.title = sheetname

  # Add column names
  # ws.append(['x', 'obo_prev', 'fgm_output_power_prev', 'Satellite'])

  for i in range(0, len(data)):
    for j in range(0, len(data[i])):
      cell = ws.cell(row=j+1, column=i+1)
      cell.value = data[i][j]
    # ws.append([x[i], obo_prev[i], fgm_output_power_prev[i], satellite_name])

  wb.save(filename)


####################
##### Math

def re_sample_vector(vector, sample_rate):
  fist = vector[0]
  last = vector[-1]

  N=sample_rate
  R = last - fist
  S = R/N

  new_vector = []
  new_vector.append(vector[0])

  for i in range(0, sample_rate):
    new_val = new_vector[i] + S
    new_vector.append(new_val)

  new_vector_rounded = [round(num, 2) for num in new_vector]

  return new_vector_rounded

def find_closest_range(vector, x):
  distance_vect = [abs(val - x) for val in vector]
  min_distance, min_distance_index = min((val, idx) for (idx, val) in enumerate(distance_vect))

  if vector[min_distance_index] < x:
    return min_distance_index,  min_distance_index+1
  else:
    return min_distance_index-1, min_distance_index

def interpolate_y_at_x(x_vec, y_vec, val):
  min_index, max_index = find_closest_range(x_vec, val)
  new_y = y_vec[min_index] + (y_vec[max_index] - y_vec[min_index])*(val - x_vec[min_index])/(x_vec[max_index] - x_vec[min_index])
  return round(new_y, 2)

def interpolate_y_axis(x_vec, new_x_vec, y_vec):
  new_y_vec = []
  new_y_vec.append(y_vec[0])
  for i in range(1, len(new_x_vec)-1):
    val = new_x_vec[i]
    new_y = interpolate_y_at_x(x_vec, y_vec, val)
    new_y_vec.append(round(new_y, 2))
  new_y_vec.append(y_vec[-1])
  return new_y_vec


####################
##### General code
def get_files_in_directory(directory_path):
  f = []
  for (dirpath, dirnames, filenames) in os.walk(directory_path):
      f.extend(filenames)
      break 
  return f

def resample_file(satellite_name, file_path, output_file_path):
  data_lines = extract_data_from_file(file_path)
  x_axis, y1_axis, y2_axis = data_lines_to_vectors(data_lines)

  txp = get_txp_from_file_name(file_path)

  # print('x', x_axis)

  x_36 = re_sample_vector(x_axis, 36)
  x_72 = re_sample_vector(x_axis, 72)

  new_x_axis = x_36[0:18] + x_72[35:]
  # print('new_x', new_x_axis)

  new_y1_axis = interpolate_y_axis(x_axis, new_x_axis, y1_axis)
  # print('new_y1', new_y1_axis)

  new_y2_axis = interpolate_y_axis(x_axis, new_x_axis, y2_axis)
  # print('new_y2', new_y2_axis)

  new_x_axis_offseted = new_x_axis[1:]
  new_y1_axis_offseted = new_y1_axis[1:]
  new_y2_axis_offseted = new_y2_axis[1:]

  x_col = ['x']
  x_col.extend(new_x_axis)

  y1_col = ['obo_prev']
  y1_col.extend(new_y1_axis)

  y2_col = ['fgm_output_power_prev']
  y2_col.extend(new_y2_axis)

  x_offseted_col = ['x2']
  x_offseted_col.extend(new_x_axis_offseted)

  y1_offseted_col = ['obo_next']
  y1_offseted_col.extend(new_y1_axis_offseted)

  y2_offseted_col = ['fgm_output_power_next']
  y2_offseted_col.extend(new_y2_axis_offseted)

  satellite_col = ['Satellite']
  satellite_col.extend([satellite_name] * len(new_x_axis))

  txp_col = ['txp']
  txp_col.extend([txp] * len(new_x_axis))

  data = [
    x_col,
    y1_col,
    y2_col,
    satellite_col,
    txp_col,
    x_offseted_col,
    y1_offseted_col,
    y2_offseted_col
  ]

  # save_excel(output_file_path, 'resampled data', satellite_name, new_x_axis, new_y1_axis, new_y2_axis, new_x_axis_offseted, new_y1_axis_offseted, new_y2_axis_offseted)
  save_excel(output_file_path, 'resampled data', data)


def resample_directory(input_directory, output_directory):
  files = get_files_in_directory(input_directory)

  if not os.path.exists(output_directory):
    os.makedirs(output_directory)

  satellite_name = input_directory.split('/')[-1]

  for f in files:
    file_path = os.path.join(input_directory, f)
    output_file_path = os.path.join(output_directory, f + '.xlsx')
    resample_file(satellite_name, file_path, output_file_path)
    print(output_file_path)





parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input-directory', dest='input_directory', required=True, help="input directory")
parser.add_argument('-o', '--output-directory', dest='output_directory', required=True, help="output directory")
args = parser.parse_args()

print('input_directory', args.input_directory)
print('output_directory', args.output_directory)

resample_directory(args.input_directory, args.output_directory)

# resample_directory('/Users/elmehdielhaij/learn/eric/input', '/Users/elmehdielhaij/learn/eric/o')




