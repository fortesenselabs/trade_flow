"""
    Model 1:
        Environement: 1
        Strategy: 2
            RL Algorithm - PPO
    Model Notes:
       
"""
import numpy as np
# import tensorflow as tf

from ray.rllib.utils.annotations import override
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.models.tf.misc import normc_initializer
from ray.rllib.models.tf.tf_modelv2 import TFModelV2
from ray.rllib.utils.framework import try_import_tf

tf1, tf, tfv = try_import_tf()
tf.compat.v1.disable_eager_execution()
tf1.disable_v2_behavior()

class BatchNormModel(TFModelV2):
    """Example of a TFModelV2 that is built w/o using tf.keras.
    NOTE: The above keras-based example model does not work with PPO (due to
    a bug in keras related to missing values for input placeholders, even
    though these input values have been provided in a forward pass through the
    actual keras Model).
    All Model logic (layers) is defined in the `forward` method (incl.
    the batch_normalization layers). Also, all variables are registered
    (only once) at the end of `forward`, so an optimizer knows which tensors
    to train on. A standard `value_function` override is used.
    """

    capture_index = 0

    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        super().__init__(obs_space, action_space, num_outputs, model_config, name)
        # Have we registered our vars yet (see `forward`)?
        self._registered = False
        self.size = int(np.product(obs_space.shape))

    @override(ModelV2)
    def forward(self, input_dict, state, seq_lens):
        last_layer = input_dict["obs_flat"]
        # inputs = tf1.keras.layers.Input(shape=(self.size,), name="inputs")
        # last_layer = inputs
        hiddens = [256, 256]
        with tf1.variable_scope("model", reuse=tf1.AUTO_REUSE):
            if isinstance(input_dict, SampleBatch):
                is_training = input_dict.is_training
            else:
                is_training = input_dict["custom_model_config"]["is_training"]
            for i, size in enumerate(hiddens):
                last_layer = tf1.layers.dense(
                    last_layer,
                    size,
                    kernel_initializer=normc_initializer(1.0),
                    activation=tf.nn.tanh,
                    name="fc{}".format(i),
                )
                # Add a batch norm layer
                last_layer = tf1.layers.batch_normalization(
                    last_layer, training=is_training, name="bn_{}".format(i)
                )

            output = tf1.layers.dense(
                last_layer,
                self.num_outputs,
                kernel_initializer=normc_initializer(0.01),
                activation=None,
                name="out",
            )
            self._value_out = tf1.layers.dense(
                last_layer,
                1,
                kernel_initializer=normc_initializer(1.0),
                activation=None,
                name="vf",
            )

        # Register variables.
        # NOTE: This is not the recommended way of doing things. We would
        # prefer creating keras-style Layers like it's done in the
        # `KerasBatchNormModel` class above and then have TFModelV2 auto-detect
        # the created vars. However, since there is a bug
        # in keras/tf that prevents us from using that KerasBatchNormModel
        # example (see comments above), we do variable registration the old,
        # manual way for this example Model here.
        if not self._registered:
            # Register already auto-detected variables (from the wrapping
            # Model, e.g. DQNTFModel).
            self.register_variables(self.variables())
            # Then register everything we added to the graph in this `forward`
            # call.
            self.register_variables(
                tf1.get_collection(
                    tf1.GraphKeys.TRAINABLE_VARIABLES, scope=".+/model/.+"
                )
            )
            self._registered = True

        return output, []

    @override(ModelV2)
    def value_function(self):
        return tf.reshape(self._value_out, [-1])