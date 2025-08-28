import copy
import datetime
import inspect
import json
import numbers
import os
from inspect import cleandoc

from server import PromptServer

root_dir = os.path.dirname(inspect.getfile(PromptServer))


class RecordModels:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tulple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tulple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
        Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
        The type can be a list for selection.

        Returns: `dict`:
            - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
            - Value input_fields (`dict`): Contains input fields config:
                * Key field_name (`string`): Name of a entry-point method's argument
                * Value field_config (`tuple`):
                    + First value is a string indicate the type of field or a list for selection.
                    + Secound value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "image": ("Image", {"tooltip": "Image pass-through input"}),
                "out_file": (
                    "STRING",
                    {
                        "multiline": False,  # True if you want the field to look like the one on the ClipTextEncode node
                        "default": "metadata-statistics/stats.json",
                    },
                ),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE",)
    # RETURN_NAMES = ("image_output_name",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "record_models"

    # OUTPUT_NODE = False
    # OUTPUT_TOOLTIPS = ("",) # Tooltips for the output node

    CATEGORY = "metadata"

    def record_models(self, image, out_file, extra_pnginfo=None):
        if extra_pnginfo is None:
            print("Missing extra_pnginfo")
            return (image,)

        res = {
            "loras": {},
            "checkpoints": {},
        }

        for val in extra_pnginfo.values():
            if val["class_type"] == "Power Lora Loader (rgthree)":
                for key, input in val["inputs"].items():
                    if key.startswith("lora_") and input["on"]:
                        lora_name = input["lora"]
                        curr = res["loras"].get(lora_name, {"count": 0, "when": []})
                        curr["count"] += 1
                        curr["when"] += datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
                        res["loras"][lora_name] = curr

            elif val["class_type"] == "CheckpointLoaderSimple":
                checkpoint_name = val["inputs"]["ckpt_name"]
                curr = res["checkpoints"].get(checkpoint_name, {"count": 0, "when": []})
                curr["count"] += 1
                curr["when"] += datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
                res["checkpoints"][checkpoint_name] = curr

        out_path = f"{root_dir}/{out_file}"
        if not os.path.isfile(out_path):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path) as f:
                f.write(json.dumps(res))
        else:
            f = open(out_path, "r+")
            db = json.load(f)
            f.close()

            final = self.merge_dicts(db, res)
            f = open(out_path, "w+")
            json.dump(final, f)
            f.close()

        return (image,)

    def merge_dicts(self, this, that):
        res = copy.deepcopy(this)
        for key in this.keys() & that.keys():
            old = res[key]
            new = that[key]
            if isinstance(old, dict) and isinstance(new, dict):
                res[key] = self.merge_dicts(old, new)
            elif (isinstance(old, numbers.Number) and isinstance(new, numbers.Number)) or (isinstance(old, list) and isinstance(new, list)):
                res[key] = old + new
            else:
                print("WARN: old and new types did not match, or were not of expected types: " + type(old) + "," + type(new))
                res[key] = new

        return res

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """
    # @classmethod
    # def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {"RecordModels": RecordModels}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {"RecordModels": "Record Models"}
