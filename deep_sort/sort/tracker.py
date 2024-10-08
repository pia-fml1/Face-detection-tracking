# vim: expandtab:ts=4:sw=4
from __future__ import absolute_import
import numpy as np
from . import kalman_filter
from . import linear_assignment
from . import iou_matching
from .track import Track

class Tracker:
    """
    This is the multi-target tracker.

    Parameters
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        A distance metric for measurement-to-track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.

    Attributes
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        The distance metric used for measurement to track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of frames that a track remains in initialization phase.
    kf : kalman_filter.KalmanFilter
        A Kalman filter to filter target trajectories in image space.
    tracks : List[Track]
        The list of active tracks at the current time step.

    """
    def __init__(self, metric, max_iou_distance=0.75, max_age=50, n_init=1):
        self.metric = metric
        self.max_iou_distance = max_iou_distance
        self.max_age = max_age
        self.n_init = n_init

        self.kf = kalman_filter.KalmanFilter()
        self.tracks = []
        self._next_id = 1

    def predict(self):
        # STEP 1: at each time T, firstly we predict x' of each Track obj with KF
        """Propagate track state distributions one time step forward.

        This function should be called once every time step, before `update`.
        """
        for track in self.tracks:
            # for each obj, predict state on time T with KF based on t-1
            track.predict(self.kf)  # Only update the KF parameter mean variance, appearance feature or before

    def update(self, detections):
        # STEP 2: Then we update
        """Perform measurement update and track management.

        Parameters
        ----------
        detections : List[deep_sort.detection.Detection]
            A list of detections at the current time step.
            each Detection obj maintain the location(bbox_tlwh), confidence(conf), and appearance feature
        """
        # Run matching cascade.
        matches, unmatched_tracks, unmatched_detections = \
            self._match(detections)    # cascade matching(appearance) + IOU matching
        # Update track set.
        # MT: If the track is successful, update the KF matrix according to the current observation detection and add the current appearance feature
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(self.kf, detections[detection_idx])

        # UT: lost track, mark miss
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()

        # UD: create a new track, classify a new ID
        for detection_idx in unmatched_detections:
            #
            self._initiate_track(detections[detection_idx])     # Create new Track obj, add self.track list
        # Discard deleted tracks
        self.tracks = [t for t in self.tracks if not t.is_deleted()]

        # Update distance metric.
        active_targets = [t.track_id for t in self.tracks if t.is_confirmed()]      # Reserve the ID of the confirmed track
        features, targets = [], []
        for track in self.tracks:           # For all confirmed track objects
            if not track.is_confirmed():
                continue
            features += track.features
            targets += [track.track_id for _ in track.features] # If there are several features, just copy the ID several times
            track.features = []     # Clear the feature of the current track obj, and add a feature in the next update

        # Partially fit all confirmed tracks and update the measured distance with new data
        self.metric.partial_fit(
            np.asarray(features), np.asarray(targets), active_targets)

    def _match(self, detections):
        # Based on the appearance information and the Mahalanobis distance, calculate the cost matrix of the tracks predicted by the Kalman filter and the detections detected at the current moment
        def gated_metric(tracks, dets, track_indices, detection_indices):
            # Tracks
            features = np.array([dets[i].feature for i in detection_indices])   # The appearance feature observed in the current frame
            # (number of people detected, 512)
            #print("----------->",features)
            targets = np.array([tracks[i].track_id for i in track_indices])     #
            #print("----------->",targets)
            # Based on the appearance information, calculate the cosine distance cost matrix of tracks and detections
            cost_matrix = self.metric.distance(features, targets)   # (number of people in track, number of people detected)
            #print("cost_matrix",cost_matrix)
            #Based on the Mahalanobis distance, filter out some inappropriate items in the cost matrix (set it to a large value)
            cost_matrix = linear_assignment.gate_cost_matrix(
                self.kf, cost_matrix, tracks, dets, track_indices,
                detection_indices)

            return cost_matrix

        """
        KF predict 
            -- confirmed 
                Matching_Cascade (appearance feature + distance)
                    -- matched Tracks  成功匹配
                    -- unmatched tracks
                        -- 
                    -- unmatched detection
            -- unconfirmed 
        """

        # Split track set into confirmed and unconfirmed tracks. ********************************************
        confirmed_tracks = [
            i for i, t in enumerate(self.tracks) if t.is_confirmed()]   # confirmed: directly apply Matching_Cascade
        unconfirmed_tracks = [
            i for i, t in enumerate(self.tracks) if not t.is_confirmed()]   # unconfirmed: directly go to IOU match
        # Associate confirmed tracks using appearance features.(Matching_Cascade) ***************************
        #Appearance features + Mahalanobis distance screening only for confirmed track
        matches_a, unmatched_tracks_a, unmatched_detections = \
            linear_assignment.matching_cascade(gated_metric, self.metric.matching_threshold, self.max_age,
                self.tracks, detections, confirmed_tracks)

        # Associate remaining tracks together with unconfirmed tracks using IOU *****************
        # for IOU match: unconfirmed + u
        iou_track_candidates = unconfirmed_tracks + [
            k for k in unmatched_tracks_a if
            self.tracks[k].time_since_update == 1]  # # just didn't match

        unmatched_tracks_a = [
            k for k in unmatched_tracks_a if
            self.tracks[k].time_since_update != 1]

        # IOU matching *************************************************************************************
        matches_b, unmatched_tracks_b, unmatched_detections = \
            linear_assignment.min_cost_matching(
                iou_matching.iou_cost, self.max_iou_distance, self.tracks,
                detections, iou_track_candidates, unmatched_detections)

        matches = matches_a + matches_b # associated matching + IOU matching
        unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
        return matches, unmatched_tracks, unmatched_detections

    def _initiate_track(self, detection):

        mean, covariance = self.kf.initiate(detection.to_xyah())    # Initialize KF according to position

        self.tracks.append(Track(
            mean, covariance, self._next_id, self.n_init, self.max_age,
            detection.feature)) # for new obj, create a new Track object for it
        self._next_id += 1
