"""
    Model 1:
        Environement: 1
        Strategy: 2
            RL Algorithm - PPO
    Model Notes:
        This model will not work in tf2 eager exection. Keras has an issue with
        how the is_training variable is passed in the model layers.
        The solution: Use model 2, which is standard tf2 without keras.
"""
import numpy as np
import tensorflow as tf

from ray.rllib.utils.annotations import override
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.models.tf.misc import normc_initializer
from ray.rllib.models.tf.tf_modelv2 import TFModelV2

class Model(TFModelV2):
    """Keras version of above BatchNormModel with exactly the same structure.
    IMORTANT NOTE: This model will not work with PPO due to a bug in keras
    that surfaces when having more than one input placeholder (here: `inputs`
    and `is_training`) AND using the `make_tf_callable` helper (e.g. used by
    PPO), in which auto-placeholders are generated, then passed through the
    tf.keras. models.Model. In this last step, the connection between 1) the
    provided value in the auto-placeholder and 2) the keras `is_training`
    Input is broken and keras complains.
    Use the below `BatchNormModel` (a non-keras based TFModelV2), instead.
    """

    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        super().__init__(obs_space, action_space, num_outputs, model_config, name)
        # get the flattened size of the inputs (allows for matrix input values)
        self.size = int(np.product(obs_space.shape))
        # create the input layer
        inputs = tf.keras.layers.Input(shape=(self.size,), name="inputs")
        # Have to batch the is_training flag (its batch size will always be 1).
        is_training = tf.keras.layers.Input(
            shape=(), dtype=tf.bool, batch_size=1, name="is_training"
        )
        # normalise the input layer
        data_mean = model_config["custom_model_config"]["mean"]
        data_variance = model_config["custom_model_config"]["var"]
        norm = tf.keras.layers.Normalization(axis=-1, mean=data_mean, variance=data_variance)(inputs)
        last_layer = norm
        hiddens = [128, 128]
        # for each hidden layer
        for i, size in enumerate(hiddens):
            label = "fc{}".format(i)
            # create the layer and attach it to the last layer
            last_layer = tf.keras.layers.Dense(
                units=size,
                kernel_initializer=normc_initializer(1.0),
                activation=tf.nn.tanh,
                name=label,
            )(last_layer)
            # Add a batch norm layer and update it to be added as the last layer
            last_layer = tf.keras.layers.BatchNormalization()(
                last_layer, 
                training=is_training
            )
        output = tf.keras.layers.Dense(
            units=self.num_outputs, # 2
            kernel_initializer=normc_initializer(0.01),
            activation=None,
            name="logits",
        )(last_layer)
        value_out = tf.keras.layers.Dense(
            units=1,
            kernel_initializer=normc_initializer(0.01),
            activation=None,
            name="value_out",
        )(last_layer)

        self.base_model = tf.keras.models.Model(
            inputs=[inputs, is_training], outputs=[output, value_out]
        )

    @override(ModelV2)
    def forward(self, input_dict, state, seq_lens):
        if isinstance(input_dict, SampleBatch):
            is_training = input_dict.is_training
        else:
            is_training = input_dict["is_training"]
       
        # logits should be (<batch size>,2) -> (32, 2)
        # values should be (<batch size>,1) -> (32, 1)
        logits, values = self.base_model(
            [input_dict["obs_flat"], tf.expand_dims(is_training, 0)]
        )
        # I think we need to remove the batch dimension (32, 1) -> (32,)
        self._value_out = tf.reshape(values, [-1])
        return logits, []

    @override(ModelV2)
    def value_function(self):
        return tf.reshape(self._value_out, [-1])