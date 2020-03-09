import os
import sys

sys.path.append('/home/Aiham.Taleb/workspace/self-supervised-3d-tasks/')
from pathlib import Path

import tensorflow.keras as keras

from self_supervised_3d_tasks.data.image_2d_loader import DataGeneratorUnlabeled2D
from self_supervised_3d_tasks.data.make_data_generator import get_data_generators
from self_supervised_3d_tasks.data.numpy_3d_loader import DataGeneratorUnlabeled3D
from self_supervised_3d_tasks.keras_algorithms import cpc, jigsaw, relative_patch_location, rotation, exemplar
from self_supervised_3d_tasks.keras_algorithms.custom_utils import get_writing_path
from self_supervised_3d_tasks.keras_algorithms.custom_utils import init

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "3"

keras_algorithm_list = {
    "cpc": cpc,
    "jigsaw": jigsaw,
    "rpl": relative_patch_location,
    "rotation": rotation,
    "exemplar": exemplar
}

data_gen_list = {
    "kaggle_retina": DataGeneratorUnlabeled2D,
    "pancreas3d": DataGeneratorUnlabeled3D,
    "brats": DataGeneratorUnlabeled3D,
    "ukb": DataGeneratorUnlabeled3D
}


def get_dataset(data_dir, batch_size, f_train, f_val, train_val_split, dataset_name,
                train_data_generator_args={}, val_data_generator_args={}, **kwargs):
    data_gen_type = data_gen_list[dataset_name]

    train_data, validation_data = get_data_generators(data_dir, train_split=train_val_split,
                                                      train_data_generator_args={**{"batch_size": batch_size,
                                                                                    "pre_proc_func": f_train},
                                                                                 **train_data_generator_args},
                                                      val_data_generator_args={**{"batch_size": batch_size,
                                                                                  "pre_proc_func": f_val},
                                                                               **val_data_generator_args},
                                                      data_generator=data_gen_type)

    return train_data, validation_data


def train_model(algorithm, data_dir, dataset_name, root_config_file, epochs=250, batch_size=2, train_val_split=0.9,
                base_workspace="~/workspace/self-supervised-3d-tasks/", save_checkpoint_every_n_epochs=5,
                **kwargs):
    kwargs["root_config_file"] = root_config_file

    working_dir = get_writing_path(Path(base_workspace).expanduser() / (algorithm + "_" + dataset_name),
                                   root_config_file)
    algorithm_def = keras_algorithm_list[algorithm].create_instance(**kwargs)

    f_train, f_val = algorithm_def.get_training_preprocessing()
    train_data, validation_data = get_dataset(data_dir, batch_size, f_train, f_val, train_val_split, dataset_name,
                                              **kwargs)
    model = algorithm_def.get_training_model()
    model.summary()

    # plot_model(model, to_file=expanduser("~/workspace/test.png"), expand_nested=True, show_shapes=True)
    # uncomment if you want to plot the model

    tb_c = keras.callbacks.TensorBoard(log_dir=str(working_dir))
    mc_c = keras.callbacks.ModelCheckpoint(str(working_dir / "weights-improvement-{epoch:03d}.hdf5"),
                                           monitor="val_loss",
                                           mode="min", save_best_only=True)  # reduce storage space
    mc_c_epochs = keras.callbacks.ModelCheckpoint(str(working_dir / "weights-{epoch:03d}.hdf5"),
                                                  period=save_checkpoint_every_n_epochs)  # reduce storage space
    callbacks = [tb_c, mc_c, mc_c_epochs]

    # Trains the model
    model.fit_generator(
        generator=train_data,
        steps_per_epoch=len(train_data),
        validation_data=validation_data,
        validation_steps=len(validation_data),
        epochs=epochs,
        callbacks=callbacks
    )


if __name__ == "__main__":
    init(train_model)
