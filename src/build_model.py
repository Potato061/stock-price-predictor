import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "../src")
from engine_init import get_engine, TableFetcher
from temporal_split import temporal_split_
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth must be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("Dynamic memory growth enabled")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)

def load_sequences():
    X_train = np.load("models/data/X_train.npy")
    y_train = np.load("models/data/y_train.npy")
    X_test = np.load("models/data/X_test.npy")
    y_test = np.load("models/data/y_test.npy")

    return (X_train, y_train), (X_test, y_test)



model = tf.keras.Sequential([
    tf.keras.layers.Conv1D(filters=64, kernel_size=3, strides=1, padding="same", activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Conv1D(filters=128, kernel_size=3, strides=1, padding="same", activation="relu"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.GlobalAveragePooling1D(),

    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(1),
])


early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True,
    min_delta=1e-4
)

checkpoint = tf.keras.callbacks.ModelCheckpoint(
    "models/saved/best_model.h5",
    monitor="val_loss",
    save_best_only=True,
    verbose=1
)

optimizer = tf.keras.optimizers.SGD(learning_rate=1e-5, momentum=0.9)
model.compile(optimizer=optimizer,loss=tf.keras.losses.Huber(),metrics=['mse'])


batch_size = 32
(X_train, y_train), (X_test, y_test) = load_sequences()

model.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=50,
    batch_size=batch_size,
    callbacks=[checkpoint, early_stopping],
)

best_model = tf.keras.models.load_model("models/saved/best_model.h5")

test_loss, test_mse = best_model.evaluate(X_test, y_test)
print(f"Test Loss: {test_loss} | Test MSE: {test_mse}")

# Predict
y_pred = best_model.predict(X_test)
print(f"Predictions shape: {y_pred.shape}")


import matplotlib.pyplot as plt

y_pred = best_model.predict(X_test).flatten()
y_actual = y_test

# Plot predictions vs actual
plt.figure(figsize=(15, 5))
plt.plot(y_actual[:1000], label="Actual", alpha=0.7)
plt.plot(y_pred[:1000], label="Predicted", alpha=0.7)
plt.xlabel("Time")
plt.ylabel("Return (normalized)")
plt.legend()
plt.savefig("predictions_vs_actual.png")
plt.show()

# Check prediction distribution
print(f"Predicted mean: {y_pred.mean()}, std: {y_pred.std()}")
print(f"Actual mean: {y_actual.mean()}, std: {y_actual.std()}")

# Directional accuracy — did model get the sign right?
directional_accuracy = (np.sign(y_pred) == np.sign(y_actual)).mean()
print(f"Directional Accuracy: {directional_accuracy:.2%}")