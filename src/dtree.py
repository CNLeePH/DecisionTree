#!/usr/bin/python

import csv
import argparse
import os
import sys
import math

NUMERIC = "numeric"
NOMINAL = "nominal"

CMP_LT = "CMP_LT"
CMP_EQ = "CMP_EQ"
CMP_GE = "CMP_GE"

class TNode:
    """stand for the nodes in decision tree"""
    name = ""
    data_type = ""
    ops = ""
    value = 0
    mean_value = 0
    marjor_value = 0
    leaf = False
    subtree = None


class DTree:
    """stand for a trained decision tree"""
    root = None

    def predict(self, instance):
        return True

    def load_model(self, model_path):
        print("Loading model from "+model_path+"...")

    def save_model(self, model_path):
        print("Saving model to "+model_path+"...")

    def print_model(self):
        print("print decision tree")


class Dataset:
    """stand for a loaded dataset"""

    data_file = None
    header = None
    data = None
    header_type = {
            "winpercent": NUMERIC,
            "oppwinpercent": NUMERIC,
            "weather": NOMINAL,
            "temperature": NUMERIC,
            "numinjured": NUMERIC,
            "oppnuminjured": NUMERIC,
            "startingpitcher": NOMINAL,
            "oppstartingpitcher": NOMINAL,
            "dayssincegame": NUMERIC,
            "oppdayssincegame": NUMERIC,
            "homeaway": NOMINAL,
            "rundifferential": NUMERIC,
            "opprundifferential": NUMERIC,
            "winner": NOMINAL
    }

    header_row = ["winpercent", "oppwinpercent", "weather", "temperature", "numinjured", "oppnuminjured", 
            "startingpitcher", "oppstartingpitcher", "dayssincegame", "oppdayssincegame", "homeaway", 
            "rundifferential", "opprundifferential", "winner"]
    header_index = {}

    target = "winner"
    target_values = []

    def __init__(self, path):
        with open(path, 'rb') as csvfile:
            rd = csv.reader(csvfile, delimiter=',')
            __header_row = next(rd, None)
            if __header_row:
                self.header_row = __header_row
            for idx in range(0, len(self.header_row)):
                self.header_row[idx] = self.header_row[idx].strip()
                self.header_index[self.header_row[idx]] = idx
            print(self.header_row)
            self.data = []
            print("Loading dataset...")
            for row in rd:
                #print row
                self.data.append(self.__preprocess_row(row))
                #print self.data[-1]

    def __preprocess_row(self, row):
        res = []
        for idx in range(0, len(row)):
            tname = self.header_type[self.header_row[idx]]
            tdata = row[idx]
            if tdata == '?':
                tdata = None
            if tname == NOMINAL:
                res.append(tdata)
            elif tname == NUMERIC:
                if tdata:
                    tdata = float(tdata)
                res.append(tdata)
            else:
                print("ERROR: UKNOW HEADER => "+tname)
                sys.exit(0)
        return res

    def __postprocess_row(self, row):
        res = []
        for item in row:
            if item != None:
                res.append(item)
            else:
                res.append('?')
        return res
        
    def save_dataset(self, outfile):
        with open(outfile, 'w') as csvfile:
            print("Saving dataset to "+outfile+"...")
            wr = csv.writer(csvfile, delimiter=',')
            wr.writerow(self.header_row)
            for row in self.data:
                wr.writerow(self.__postprocess_row(row))

    def train_model(self, prune):
        for row in self.data:
            val = row[self.header_index[self.target]]
            if not(val in self.target_values) and val != None:
                self.target_values.append(val)
        print "target values: ",self.target_values
        input_data = []
        count_map = {}
        for tt in self.target_values:
            count_map[tt] = 0
        for row in self.data:
            target = row[self.header_index[self.target]]
            if target != None:
                input_data.append(row)
                count_map[target] += 1
        dtree = DTree()
        dtree.root = TNode()
        self.__build_tree(dtree.root, input_data, self.__calc_entropy(count_map))
        return dtree

    def __calc_entropy(self, count_map):
        entropy = 0.0
        count = 0
        #print(count_map)
        for (key, val) in count_map.items():
            count += val
        if count == 0:
            print("entrop == 0 ??!!!")
            sys.exit(0)
        count = float(count)
        for (key, val) in count_map.items():
            if val == 0:
                continue
            p = val / count
            #print("proba => "+str(p))
            entropy += -p*math.log(p, 2)
        #print("entrop => "+str(entropy))
        return entropy

    def __build_tree(self, root, dataset, last_entropy):
        if self.__is_pure(dataset):
            root.leaf = True
            return
        print "continue"
        # need to branch again
        # probe is actually a dict has keys {title, gain, values => [], entropy}
        root.leaf = False
        root.subtree = []
        probe_list = []
        for title in self.header_row:
            if title != self.target:
                probe_item = self.__probe_title(title, dataset, last_entropy)
#                print probe_item
                probe_list.append(probe_item)

        assert(len(probe_list) > 0)
        max_gain = probe_list[0]["gain"]
        max_candidate = probe_list[0]
        for candidate in probe_list:
            if max_gain < candidate["gain"]:
                max_gain = candidate["gain"]
                max_candidate = candidate
        print max_candidate

        # TODO: construct the subtrees


    def __is_pure(self, dataset):
        res  = {}
        print "is pure"
        for row in dataset:
            val = row[self.header_index[self.target]]
            if val != None:
                res[val] = True
        print "length: ",res
        return len(res) == 1

    def __probe_title(self, title, dataset, last_entropy):
        res = {"title":title}
        dat = []
        vals = []
        val_count = {}
        target_count = {}
        dtype = self.header_type[title]
        if dtype == NUMERIC:
            for tt in self.target_values:
                val_count[tt] = 0
        for row in dataset:
            val = row[self.header_index[title]]
            target = row[self.header_index[self.target]]
            if val != None and target != None:
                dat.append(row[self.header_index[title]])
                if dtype == NOMINAL:
                    if val in val_count:
                        val_count[val] += 1
                    else:
                        val_count[val] = 1
                        vals.append(val)
                        target_count[val] = {}
                        for tt in self.target_values:
                            target_count[val][tt] = 0
                    target_count[val][target] += 1
                elif dtype == NUMERIC:
                    vals.append(val)
                    if val in target_count:
                        target_count[val][target] += 1
                    else:
                        target_count[val] = {}
                        for tt in self.target_values:
                            target_count[val][tt] = 0
                        target_count[val][target] += 1
                    val_count[target] += 1
                else:
                    print("UNKNOWN data type: "+dtype)
                    sys.exit(1)
        if dtype == NOMINAL:
            sum_sum = 0.0
            ent_sum = 0.0
            for (key, val) in val_count.items():
                sum_sum += val
            for (key, val) in val_count.items():
                ent_sum += self.__calc_entropy(target_count[key]) * val / sum_sum
            #split_ent = self.__calc_entropy(val_count)
            split_ent = 1
            print split_ent
            res["entropy"] = ent_sum
            res["gain"] = (last_entropy - ent_sum) / split_ent
            mval = max(val_count, key=val_count.get)
            res["mean_value"] = mval
            res["marjor_value"] = mval
            res["values"] = list(val_count.keys())
        elif dtype == NUMERIC:
            acc = {}
            for tt in self.target_values:
                acc[tt] = 0
            means_val = 0
            for item in vals:
                means_val += item
            means_val = means_val / float(len(vals))
            val_set = set(vals)
            vals = list(val_set)
            vals.sort()
            min_mid_val = None
            min_gain = None
            min_entropy = None
            for idx in range(0, len(vals)-1):
                prev_val = vals[idx]
                next_val = vals[idx + 1]
                mid_val = (prev_val + next_val) / 2.0
                prev_sum = 0.0
                next_sum = 0.0
                for tt in self.target_values:
                    acc[tt] += target_count[prev_val][tt]
                    val_count[tt] -= target_count[prev_val][tt]
                    prev_sum += acc[tt]
                    next_sum += val_count[tt]
                prev_ent = self.__calc_entropy(acc)
                next_ent = self.__calc_entropy(val_count)
                #split_ent = self.__calc_entropy({1:prev_sum, 2:next_sum})
                split_ent = 1
                sum_sum = prev_sum + next_sum
                cur_entropy = prev_ent * prev_sum / sum_sum + next_ent * next_sum / sum_sum
                gain = (last_entropy - cur_entropy) / split_ent
                if min_gain == None or min_gain < gain:
                    min_gain = gain
                    min_mid_val = mid_val
                    min_entropy = cur_entropy
#                    if title == "oppnuminjured":
#                        print ">>>>>>>>>>>>>",split_ent, [prev_sum,next_sum], vals, prev_val, next_val, mid_val
            res["gain"] = min_gain
            res["entropy"] = min_entropy
            res["values"] = [min_mid_val]
            res["mean_value"] = means_val
            res["marjor_value"] = means_val
        else:
            print("unknown data type"+dtype)
            sys.exit(1)
        return res

    def __split_title(self, title):
        pass


    def predict(self):
        pass

    def validate(self):
        pass


def main(args):
    print(args)
    if args["action"] == "train":
        print("Do training")
        if os.path.isfile(args["input"]):
            print(args["input"]+" is a file")
            dataset = Dataset(args["input"])
            model = dataset.train_model(args["prune"])
            if args["print"]:
                mode.print_model()
            if len(args["model"]) > 0 :
                model.save_model(args["model"])
            if len(args["output"]) > 0 :
                dataset.save_dataset(args["output"])
        else:
            print("wrong input file: "+args["input"])
    elif args["action"] == "validate":
        if os.path.isfile(args["input"]) and os.path.isfile(args["model"]):
            print("Do validation")
        else:
            print("wrong input file: "+args["input"]+"or wrong model file: "+args["model"])
        pass
    elif args["action"] == "predict":
        if os.path.isfile(args["input"]) and os.path.isfile(args["model"]):
            print("Do prediction")
        else:
            print("wrong input file: "+args["input"]+"or wrong model file: "+args["model"])
        pass
    else:
        print("UNKNOWN ACTION: " + args["action"])
    print("Done.")


if __name__ == "__main__":
    opt_parser = argparse.ArgumentParser(description="Train, test or validate the input dataset using C4.5 decision tree algorithm")
    opt_parser.add_argument('-a', '--action', dest='action', type=str, default='train', choices=['train','validate','predict'], required=True, help='specify the action')
    opt_parser.add_argument('-i', '--input', dest='input', type=str, default='', help='specify the input file(dataset)')
    opt_parser.add_argument('-o', '--output', dest='output', type=str, default='', help='specify the output file(dataset)')
    opt_parser.add_argument('-m', '--model', dest='model', type=str, default='', help='specify the trained model')
    opt_parser.add_argument('--prune', dest='prune', action='store_true', help='whether or not to prune the tree')
    opt_parser.add_argument('--print', dest='print', action='store_true', help='whether or not to print the generated decision tree')
    args = opt_parser.parse_args()
    params = vars(args)
    main(params)
