# hfx local street speeds

This little project is a collection of motor vehicle speeds, as collected by a DIY speed camera. The purpose of this project was to turn anecdotal and personal observations from myself & neighbours into real data.

Additionally, it is understood that the city of Halifax does not publish a rich dataset on this topic. [Halifax Traffic Calming Assessments](https://data-hrm.hub.arcgis.com/datasets/HRM::traffic-calming-assessments/explore) provides an open data set, but it lacks particular details.

Although a DIY device can be imperfect, the methods used have been employed by a large community of enthusiasists andthere is calibration done for each data capture. In understanding that there may be accurracy issues, the aim is to keep a minimal degree of imprecision.


## Experiment Scope & Constraints

* All roads observed were one lane and in residential communities. The roads are typically wide and there are marginal instances of two vehicles passing at the same time, although this is rare.
* For each observation, the camera was placed on a window sill between xx-xx metres from the road being observed. For each experiment, calibration of the camera to account for the adjustment in distance was made.

## The Device

The device is a Raspberry Pi Model 4, a camera module, and a case. Software is written by Claude Pageau and is [open source on GitHub](https://github.com/pageauc/speed-camera). This software is actively maintained and continues to improve with quality discussion and amendments.


## References

* https://data-hrm.hub.arcgis.com/datasets/HRM::traffic-calming-assessments/explore
* https://www.mikeontraffic.com/85th-percentile-speed-explained/
* https://www.strongtowns.org/journal/2020/7/24/understanding-the-85th-percentile-speed
