import tkinter as tk
from tkinter import filedialog, ttk
import tensorflow as tf
import numpy as np
from PIL import Image, ImageTk
from keras.src.callbacks import ModelCheckpoint
from keras.src.legacy.preprocessing.image import ImageDataGenerator
from keras.src.saving import load_model
from keras.src.utils import load_img, img_to_array
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ImageClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CNN Image Classifier")

        self.datagen = create_image_generator()
        self.test_datagen = ImageDataGenerator(rescale=1. / 255)
        self.test_datagen1 = ImageDataGenerator(rescale=1. / 255)

        self.setup_widgets()

    def setup_widgets(self):
        # Model Frame
        frame_model = tk.LabelFrame(self.root, text="Model", padx=10, pady=10)
        frame_model.pack(padx=10, pady=5, fill="both", expand="yes")

        btn_create_model = ttk.Button(frame_model, text="Create New Model", command=self.create_model)
        btn_create_model.pack(side=tk.LEFT)

        btn_load_model = ttk.Button(frame_model, text="Load Trained Model", command=self.load_model)
        btn_load_model.pack(side=tk.LEFT, padx=10)

        self.loaded_accuracy_label = tk.Label(frame_model)
        self.loaded_accuracy_label.pack(side=tk.RIGHT, padx=30)

        # Training Images Dataset Frame
        frame_train = tk.LabelFrame(self.root, text="Training Images Dataset", padx=10, pady=10)
        frame_train.pack(padx=10, pady=5, fill="both", expand="yes")

        btn_load_train = ttk.Button(frame_train, text="Load Training", command=self.load_training)
        btn_load_train.pack(side=tk.LEFT)

        self.btn_load_test_set = ttk.Button(frame_train, text="Load Validation Dataset", command=self.load_validation)
        self.btn_load_test_set.pack(side=tk.LEFT, padx=10)

        self.accuracy_label = tk.Label(frame_train)
        self.accuracy_label.pack(side=tk.RIGHT, padx=30)

        # Test Image Frame
        frame_test = tk.LabelFrame(self.root, text="Test Image", padx=10, pady=10)
        frame_test.pack(padx=10, pady=5, fill="both", expand="yes")

        self.btn_load_test = ttk.Button(frame_test, text="Load Testing Image", command=self.load_and_display_test)
        self.btn_load_test.pack(side=tk.LEFT)

        self.image_label = tk.Label(frame_test)
        self.image_label.pack(side=tk.LEFT, padx=30)

        self.result_label = tk.Label(frame_test)
        self.result_label.pack(side=tk.RIGHT, padx=30)

        # Configuration Frame
        frame_config = tk.LabelFrame(self.root, text="Configuration", padx=10, pady=10)
        frame_config.pack(padx=10, pady=5, fill="both", expand="yes")

        self.initial_value = tk.IntVar(value=10)
        tk.Label(frame_config, text="Epochs:").pack(side=tk.LEFT)
        self.entry_epochs = ttk.Spinbox(frame_config, from_=10, to=30, width=5, textvariable=self.initial_value, wrap=False)
        self.entry_epochs.pack(side=tk.LEFT, padx=5)

        # Train and Classify Buttons
        btn_train = ttk.Button(root, text="Train Network", command=self.train_model)
        btn_train.pack(fill='x', padx=10, pady=5)

        btn_test = ttk.Button(root, text="Classify Image", command=self.classify_img)
        btn_test.pack(fill='x', padx=10, pady=5)

        # Output Text
        self.output_text = tk.Text(self.root, height=5, background='white', foreground='black')
        self.output_text.pack(fill='both', padx=10, pady=5, expand=True)
        self.output_text.configure(font='helvetica 14')

    def create_model(self):
        self.model = create_model()

    def load_model(self):
        try:
            filetypes = [("Keras Model", "*.keras")]
            model_path = filedialog.askopenfilename(title="Open file", filetypes=filetypes)
            if model_path:
                self.model = load_model(model_path)
                val_loss, val_accuracy = self.model.evaluate(self.validation_set)
                self.output_text.insert(tk.END, "Classification model loaded successfully.\n")
                self.loaded_accuracy_label.config(text=f"Accuracy: {val_accuracy * 100:.2f}%, Loss: {val_loss * 100:.2f}%", font=("Helvetica", 14))
            else:
                self.output_text.insert(tk.END, "No file selected.\n")
        except AttributeError:
            self.output_text.insert(tk.END, "Please load a validation set first\n")

    def load_training(self):
        try:
            self.train_set = load_training_images(self.datagen)
            self.output_text.insert(tk.END, "Training images loaded successfully.\n")
        except FileNotFoundError:
            self.output_text.insert(tk.END, "Training images not found.\n")

    def load_validation(self):
        try:
            self.validation_set = load_validation_set(self.test_datagen)
            self.output_text.insert(tk.END, "Validation set loaded successfully.\n")
        except FileNotFoundError:
            self.output_text.insert(tk.END, "Validation set not found.\n")

    def train_model(self):
        try:
            epochs = int(self.entry_epochs.get())
            loss, accuracy, history = train_model(self.train_set, self.validation_set, self.model, epochs)
            self.plot_training_history(history)
            self.accuracy_label.config(text=f"Accuracy: {accuracy * 100:.2f}%, Loss: {loss * 100:.2f}%", font=("Helvetica", 14))
            self.loaded_accuracy_label.config(text="")
            self.output_text.insert(tk.END, f"Training complete with loss: {loss * 100:.2f} and accuracy: {accuracy * 100:.2f}\n")
        except Exception as e:
            self.output_text.insert(tk.END, "An error occurred! Make sure to load training and validation datasets and create or load a model.\n")
            print(e)

    def load_and_display_test(self):
        try:
            img_array, img = load_test_image(self.test_datagen1)
            if img is not None:
                img = img.resize((180, 180), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.image_label.image = photo
                self.test_img = img_array
                self.output_text.insert(tk.END, "Test image loading complete.\n")
            else:
                self.output_text.insert(tk.END, "Failed to load test image.\n")
        except FileNotFoundError:
            self.output_text.insert(tk.END, "Test image not found.\n")

    def classify_img(self):
        try:
            if self.test_img is None:
                self.output_text.insert(tk.END, "Failed to load test data.\n")
                return

            result, confidence = classify_image(self.test_img, self.model)
            self.result_label.config(text=f"Class: {result}, Confidence: {confidence:.2f}%", font=("Helvetica", 14))
            self.output_text.insert(tk.END, f"Image classified as: {result}\n")
        except AttributeError:
            self.output_text.insert(tk.END, "An error occurred! Make sure to create or load a model first\n")

    def plot_training_history(self, history):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

        ax1.plot(history.history['accuracy'], label='Training Accuracy')
        ax1.plot(history.history['val_accuracy'], label='Validation Accuracy')
        ax1.set_ylabel('Accuracy')
        ax1.set_title('Training and Validation Accuracy')
        ax1.legend()

        ax2.plot(history.history['loss'], label='Training Loss')
        ax2.plot(history.history['val_loss'], label='Validation Loss')
        ax2.set_ylabel('Loss')
        ax2.set_xlabel('Epoch')
        ax2.set_title('Training and Validation Loss')
        ax2.legend()

        fig.savefig('training_history.png')
        fig.subplots_adjust(hspace=0.5)

        plot_window = tk.Toplevel(self.root)
        plot_window.title("Training History")
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def create_model():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(128, 128, 3)),
        tf.keras.layers.Conv2D(32, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Conv2D(64, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Conv2D(128, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model

def create_image_generator():
    datagen = ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        rescale=1. / 255
    )
    return datagen

def train_model(training_images, validation_images, model, epochs):
    checkpoint_callback = ModelCheckpoint(
        'model_best.keras',
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1,
        save_weights_only=False
    )
    history = model.fit(x=training_images, validation_data=validation_images, epochs=epochs, callbacks=[checkpoint_callback])
    loss, accuracy = model.evaluate(validation_images)
    return loss, accuracy, history

def load_training_images(datagen):
    directory = filedialog.askdirectory(title="Select training data directory")
    train_generator = datagen.flow_from_directory(
        directory,
        target_size=(128, 128),
        batch_size=32,
        class_mode='binary'
    )
    return train_generator

def load_validation_set(test_datagen):
    directory = filedialog.askdirectory(title="Select test data directory")
    test_generator = test_datagen.flow_from_directory(
        directory,
        target_size=(128, 128),
        batch_size=32,
        class_mode='binary'
    )
    return test_generator

def load_test_image(test_datagen):
    filetypes = [('PNG files', '*.png'), ('JPG files', '*.jpg'), ('JPEG files', '*.jpeg')]
    image_path = filedialog.askopenfilename(title="Open file", filetypes=filetypes)

    img = load_img(image_path, target_size=(128, 128))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = next(test_datagen.flow(img_array, batch_size=1))[0]

    img = Image.fromarray((img_array * 255).astype('uint8'), 'RGB')
    return img_array, img

def classify_image(image_array, model):
    if image_array is None:
        return "No image loaded", None

    image_array = np.expand_dims(image_array, axis=0)
    predictions = model.predict(image_array)
    predicted_class = 'dog' if predictions[0, 0] > 0.5 else 'cat'
    confidence = predictions[0, 0] if predicted_class == 'dog' else 1 - predictions[0, 0]

    return predicted_class, confidence * 100

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("760x620")
    app = ImageClassifierApp(root)
    root.mainloop()
