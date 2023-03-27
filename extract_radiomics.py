"""
    ----------------------------------------
    GTVNSCLC - Radiomic feature extraction
    ----------------------------------------

    ----------------------------------------
    Author: Alberto Traverso
    Email:  alberto.traverso@maastro.nl
    ----------------------------------------

"""
import os
import sys

import tqdm
import time
import argparse
import multiprocessing
import csv
import logging

import yaml
import radiomics
from radiomics import featureextractor
import SimpleITK as sitk


## ----------------------------------------


## Function to extract radiomic features given a pair (image,mask) and store them into a json file
def extract_radiomics(image, mask, parameters,output):

  # Tell pyradiomics were to get the parameters for the extraction
  extractor=featureextractor.RadiomicsFeatureExtractor(parameters)

  # Regulate verbosity with radiomics.verbosity
  radiomics.setVerbosity(50)

  # Extract features
  result=extractor.execute(image,mask)

  # Printing to understand what is being preprocessed
  print("Processing the following image: %s" %image )
  print("Processing the following mask: %s" %mask)


  # Write the previous dictionary
  headers=None
  with open(output, 'w') as outputFile:
    writer = csv.writer(outputFile, lineterminator='\n')
    if headers is None:
      headers = list(result.keys())
      writer.writerow(headers)

    row = []
    for h in headers:
      row.append(result.get(h, "N/A"))
    writer.writerow(row)

  print("The radiomic features are stored in %s" %output)



## ----------------------------------------


def run_core(data_dict):
  pat = data_dict["pat"]
  pat_dir_path_nrrd = data_dict["pat_dir_path_nrrd"]
  ct_nrrd_path = data_dict["path_to_ct_dir"]
  mask_nrrd_path=data_dict["pat_dir_path_roi"]
  output_radiomics_path=data_dict["pat_to_out_dir"]
  verbose = data_dict["verbose"]
  parameters=data_dict["radiomics_parameters"]

  # feature extraction using extract_radiomics

  extract_radiomics(ct_nrrd_path,mask_nrrd_path,parameters,output_radiomics_path)

## ----------------------------------------

def main(config):

  nrrd_path = config["nrrd_path"]
  cpu_cores = config["cpu_cores"]
  radiomics_path=config['radiomics_output']
  excluded_list=config['excluded_patients']


  # list of patient  and roi dictionaries storing the information needed for processing
  # (required for multiprocessing)
  mp_dict_list = list()

  use_multiprocessing = True if cpu_cores > 1 else False

  # list of patients to be pre-processed
  pat_list = list()
  # list of ROIs to be pre-processed
  roi_list=list(config["rois_dict"])



  print("Looking for patient data at %s...\n\nPatients found:"%(nrrd_path))

  for f in sorted(os.listdir(nrrd_path)):
    if os.path.isdir(os.path.join(nrrd_path, f)):
      pat_list.append(f)
      print("  - ", f)
  #Remove patients (if any)
    if f in excluded_list:
      print("Excluding %s" %f)
      pat_list.remove(f)


  print("\n(for a total of %g Patients)"%(len(pat_list)))
  print("\nStarting the preprocessing...")

  for pat_num, pat in enumerate(sorted(pat_list)):
    pat_dir_path_nrrd = os.path.join(nrrd_path, pat)
    # location where the NRRD cts are located
    ct_nrrd_path = os.path.join(pat_dir_path_nrrd, pat + '_ct.nrrd')


    # sanity check
    assert os.path.exists(ct_nrrd_path)


    for roi in roi_list:
      data_dict=dict()
      pat_dir_path_seg=os.path.join(pat_dir_path_nrrd,pred_segmasks_folder_name)
      roi_dir_path_nrrd= os.path.join(pat_dir_path_seg,"%s.nrrd" %roi)
      print(roi_dir_path_nrrd)
      analysis_path=os.path.join(radiomics_path,pat,roi)
      print(analysis_path)
      if not os.path.exists(analysis_path): 
        os.makedirs(analysis_path)
      output_dir_path_csv=os.path.join(analysis_path,"%s_%s_radiomic_features.csv" % (pat,roi))

      # sanity check
      assert os.path.exists(roi_dir_path_nrrd)
    
      data_dict['pat_dir_path_roi']=roi_dir_path_nrrd
      data_dict['pat_to_out_dir']=output_dir_path_csv
      data_dict['pat']=pat
      data_dict['pat_dir_path_nrrd']=pat_dir_path_nrrd
      data_dict["path_to_ct_dir"] = ct_nrrd_path
      data_dict["radiomics_parameters"]=radiomics_config_path
      data_dict["verbose"] = False if use_multiprocessing else True



      mp_dict_list.append(data_dict)
    


    # monitor performance
  tic = time.time()

  if use_multiprocessing:
    print("\nRunning on %g cores."%(cpu_cores))
    pool = multiprocessing.Pool(processes = cpu_cores)
    for _ in tqdm.tqdm(pool.imap_unordered(run_core, mp_dict_list), total = len(mp_dict_list)):
      pass

  else:
    print("\nRunning process on a single core.")
    for data_dict in tqdm.tqdm(mp_dict_list):
      run_core(data_dict)

  toc = time.time()
  elapsed = toc - tic

  print('\nTask completed in %.2f seconds.'%(elapsed))

## ----------------------------------------
## ----------------------------------------

if __name__ == '__main__':

  base_conf_file_path = '.'

  parser = argparse.ArgumentParser(description = 'GTVNSCLC radiomics - Radiiomics extraction step')

  parser.add_argument('--conf',
                      required = False,
                      help = 'Specify the path to the YAML configuration file containing the run details.',
                      default = "config_radiomics_extraction.yaml"
                     )

  args = parser.parse_args()

  conf_file_path = os.path.join(base_conf_file_path, args.conf)

  with open(conf_file_path) as f:
    yaml_conf = yaml.load(f, Loader = yaml.FullLoader)

  # base data directory
  data_base_path = yaml_conf["data"]["base_path"]

  # nrrd data directory
  nrrd_path = yaml_conf["data"]["nrrd_base_path"]
  pred_segmasks_folder_name = yaml_conf["data"]["pred_segmasks_folder_name"]

  # ROIs dictionary
  rois_dict = yaml_conf['data']["rois_to_input"]

  # Radiomics config_path
  radiomics_config_path=yaml_conf['radiomics']['config_path']

  # Radiomics out_path
  radiomics_out_path=yaml_conf['radiomics']['radiomics_out_path']

  # Ecluded patients
  excluded_patients=yaml_conf['data']['excluded_patients']



# dictionary to be passed to the main function
  config = dict()

  config["nrrd_path"] = nrrd_path
  config["pred_segmasks_folder_name"] = pred_segmasks_folder_name
  config["rois_dict"] = rois_dict
  config["radiomics_parameters"]=radiomics_config_path
  config['radiomics_output']=radiomics_out_path
  config['excluded_patients']=excluded_patients

  # cores to use for multiprocessing
  config["cpu_cores"] = yaml_conf["proc"]["cpu_cores"]

  main(config)
