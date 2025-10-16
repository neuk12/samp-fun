#!/usr/bin/env python3
import time
import json
import numpy as np
from libsick import SickScan
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, griddata
from scipy.ndimage import gaussian_filter1d

class VehicleDetector:
    def __init__(self, config_file, min_length=2.0, min_width=1.0,
                 min_points=3, max_gap=1.5, height_points=5, movement_thresh=0.2):
        with open(config_file, "r") as f:
            config = json.load(f)

        self.scanner_width = None
        self.scanner_large = None

        for laser in config["lasers"]:
            scanner = SickScan(ip=laser["ip"], port=laser["port"])
            scanner.set_start_stop_angle(laser["start_angle"], laser["stop_angle"])
            if laser["type"] == "width":
                self.scanner_width = scanner
            elif laser["type"] == "large":
                self.scanner_large = scanner

        if not self.scanner_width or not self.scanner_large:
            raise ValueError("Falta definir láser 'width' o 'large' en el JSON.")

        # Estados de detección
        self.vehiculo_en_proceso = False
        self.last_detection_time = 0
        self.last_front_distance = None

        # Config
        self.min_length = min_length
        self.min_width = min_width
        self.min_points = min_points
        self.max_gap = max_gap
        self.height_points = height_points
        self.movement_thresh = movement_thresh
        self.laser_height = 0.0

        # Acumulación slices 3D
        self.all_X = []
        self.all_Y = []
        self.all_Z = []

        # Figura 3D
        self.fig = None
        self.ax = None

    def capture_baseline(self, samples=100, delay=0.05):
        print("📏 Capturando baseline de los láseres...")
        width_values, width_angles = [], []
        for _ in range(samples):
            angles, values = self.scanner_width.extract_telegram(self.scanner_width.scan())
            width_values.append(values)
            width_angles.append(angles)
            time.sleep(delay)
        self.baseline_width = np.mean(np.array(width_values), axis=0)
        self.noise_width = np.std(np.array(width_values), axis=0)
        self.baseline_angles_width = np.mean(np.array(width_angles), axis=0)

        large_values, large_angles = [], []
        for _ in range(samples):
            angles, values = self.scanner_large.extract_telegram(self.scanner_large.scan())
            large_values.append(values)
            large_angles.append(angles)
            time.sleep(delay)
        self.baseline_large = np.mean(np.array(large_values), axis=0)
        self.noise_large = np.std(np.array(large_values), axis=0)
        self.baseline_angles_large = np.mean(np.array(large_angles), axis=0)

        idx_vertical = np.argmin(np.abs(self.baseline_angles_width - 90))
        self.laser_height = float(self.baseline_width[idx_vertical])
        print(f"✅ Baseline capturada correctamente. Altura láser definida: {self.laser_height:.2f} m")

    def get_largest_cluster(self, points):
        if len(points) == 0:
            return np.array([])
        pts = np.sort(points)
        gaps = np.diff(pts)
        clusters = []
        cur = [pts[0]]
        for i, g in enumerate(gaps):
            if g <= self.max_gap:
                cur.append(pts[i+1])
            else:
                clusters.append(np.array(cur))
                cur = [pts[i+1]]
        clusters.append(np.array(cur))
        largest = max(clusters, key=lambda c: len(c))
        return largest if len(largest) >= self.min_points else np.array([])

    def agregar_slice_3d(self, cluster_l, cluster_w, vehicle_distances, num_slices=15):
        if len(cluster_l) == 0 or len(cluster_w) == 0 or len(vehicle_distances) == 0:
            return

        min_len = min(len(cluster_l), len(cluster_w), len(vehicle_distances))
        cluster_l = np.asarray(cluster_l[:min_len])
        cluster_w = np.asarray(cluster_w[:min_len])
        vehicle_distances = np.asarray(vehicle_distances[:min_len])

        heights = (self.laser_height - vehicle_distances).astype(float)
        median_h = np.median(heights)
        std_h = np.std(heights)
        valid_h_mask = np.abs(heights - median_h) < 1.5 * std_h
        cluster_l = cluster_l[valid_h_mask]
        cluster_w = cluster_w[valid_h_mask]
        heights = heights[valid_h_mask]

        sorted_w = np.sort(cluster_w)
        gaps = np.diff(sorted_w)
        max_gap_allowed = 0.3
        large_gaps_idx = np.where(gaps > max_gap_allowed)[0]
        if len(large_gaps_idx) > 0:
            end = large_gaps_idx[0] + 1
            mask_w = cluster_w <= sorted_w[end-1]
            cluster_w = cluster_w[mask_w]
            cluster_l = cluster_l[mask_w]
            heights = heights[mask_w]

        if len(cluster_l) < 2:
            return

        order = np.argsort(cluster_l)
        cluster_l_sorted = cluster_l[order]
        heights_sorted = heights[order]
        f_height = interp1d(cluster_l_sorted, heights_sorted, kind='linear', bounds_error=False, fill_value="extrapolate")
        slices_l = np.linspace(np.min(cluster_l_sorted), np.max(cluster_l_sorted), num_slices)

        for l in slices_l:
            z_center = float(f_height(l))
            w_dense = np.linspace(np.min(cluster_w), np.max(cluster_w), max(30, len(cluster_w)))
            z_profile = np.full_like(w_dense, z_center)
            z_smooth = gaussian_filter1d(z_profile, sigma=1.0)
            taper = np.linspace(0.0, 0.05, len(z_smooth)//2)
            z_smooth[:len(taper)] += taper
            z_smooth[-len(taper):] += taper[::-1]

            X, Y = np.meshgrid([l], w_dense)
            Z = np.array([z_smooth])
            self.all_X.append(X.flatten())
            self.all_Y.append(Y.flatten())
            self.all_Z.append(Z.flatten())

    def generar_mesh_3d(self):
        if not self.all_X or not self.all_Y or not self.all_Z:
            return

        if self.fig is None:
            self.fig = plt.figure(figsize=(9,6))
            self.ax = self.fig.add_subplot(111, projection='3d')
            plt.ion()
            plt.show()

        self.ax.clear()
        X = np.concatenate(self.all_X)
        Y = np.concatenate(self.all_Y)
        Z = np.concatenate(self.all_Z)

        xi = np.linspace(np.min(X), np.max(X), 200)
        yi = np.linspace(np.min(Y), np.max(Y), 200)
        XI, YI = np.meshgrid(xi, yi)
        ZI = griddata((X, Y), Z, (XI, YI), method='linear')
        ZI = np.nan_to_num(ZI, nan=0.0)

        self.ax.plot_surface(XI, YI, ZI, color='blue', alpha=0.8, rstride=1, cstride=1)
        self.ax.set_xlabel('X (largo)')
        self.ax.set_ylabel('Y (ancho)')
        self.ax.set_zlabel('Z (altura)')
        self.ax.set_title('Vehículo 3D')
        self.ax.set_xlim(np.min(X)-0.5, np.max(X)+0.5)
        self.ax.set_ylim(np.min(Y)-0.5, np.max(Y)+0.5)
        self.ax.set_zlim(0, self.laser_height + 1.0)
        plt.draw()
        plt.pause(0.01)

    def detectar_vehiculos(self, delay=0.05):
        # --- Láser ancho ---
        angles_w, values_w = self.scanner_width.extract_telegram(self.scanner_width.scan())
        values_w = np.array(values_w, dtype=float)
        angles_w = np.array(angles_w, dtype=float)
        threshold_w = np.mean(self.noise_width) * 4.5
        indices_w = np.where(np.abs(values_w - self.baseline_width) > threshold_w)[0]

        cluster_w = np.array([])
        vehicle_distances = np.array([])
        if len(indices_w) >= self.min_points:
            selected_vals = values_w[indices_w]
            selected_angles = angles_w[indices_w]
            y_points = selected_vals * np.sin(np.radians(selected_angles))
            cluster_w = self.get_largest_cluster(y_points)
            if cluster_w.size > 0:
                cmin, cmax = np.min(cluster_w), np.max(cluster_w)
                within_cluster = (y_points >= cmin - 1e-6) & (y_points <= cmax + 1e-6)
                vehicle_distances = selected_vals[within_cluster]
                cluster_w = y_points[within_cluster]
            else:
                vehicle_distances = np.array([])

        # --- Láser largo ---
        angles_l, values_l = self.scanner_large.extract_telegram(self.scanner_large.scan())
        values_l = np.array(values_l, dtype=float)
        angles_l = np.array(angles_l, dtype=float)
        threshold_l = np.mean(self.noise_large) * 4.5
        indices_l = np.where(np.abs(values_l - self.baseline_large) > threshold_l)[0]

        cluster_l = np.array([])
        front_distance = None
        if len(indices_l) >= self.min_points:
            selected_vals_l = values_l[indices_l]
            selected_angles_l = angles_l[indices_l]
            x_points = selected_vals_l * np.cos(np.radians(selected_angles_l))
            cluster_l = self.get_largest_cluster(x_points)
            if cluster_l.size > 0:
                front_distance = np.min(cluster_l)

        # --- Filtro de movimiento ---
        movement_detected = False
        if front_distance is not None:
            if self.last_front_distance is not None:
                movement = self.last_front_distance - front_distance
                if movement > self.movement_thresh:
                    movement_detected = True
            self.last_front_distance = front_distance

        # --- Vehículo detectado solo si hay movimiento real ---
        if movement_detected and cluster_w.size > 0 and cluster_l.size > 0:
            width_measured = np.max(cluster_w) - np.min(cluster_w)
            length_measured = np.max(cluster_l) - np.min(cluster_l)
            if vehicle_distances.size > 0:
                lowest_points = np.sort(vehicle_distances)[:self.height_points]
                height_measured = self.laser_height - np.mean(lowest_points)
                height_measured = float(np.clip(height_measured, 0.0, self.laser_height))
            else:
                height_measured = 0.0

            if length_measured >= self.min_length and width_measured >= self.min_width:
                if not self.vehiculo_en_proceso:
                    self.vehiculo_en_proceso = True
                    self.last_detection_time = time.time()
                    self.all_X.clear()
                    self.all_Y.clear()
                    self.all_Z.clear()
                    print(f"🚗 Vehículo detectado → Largo: {length_measured:.2f} | "
                          f"Ancho: {width_measured:.2f} | Altura: {height_measured:.2f}")

                self.agregar_slice_3d(cluster_l, cluster_w, vehicle_distances)
                self.last_detection_time = time.time()

        # --- Vehículo completo ---
        if self.vehiculo_en_proceso and (time.time() - self.last_detection_time > 0.6):
            print("✅ Vehículo completo. Generando mesh 3D...")
            self.generar_mesh_3d()
            self.vehiculo_en_proceso = False
            self.all_X.clear()
            self.all_Y.clear()
            self.all_Z.clear()

        time.sleep(delay)

if __name__ == "__main__":
    detector = VehicleDetector("lasers_config.json")
    detector.capture_baseline()
    print("🚦 Esperando vehículos...\n")
    while True:
        detector.detectar_vehiculos()
