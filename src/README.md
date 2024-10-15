Inspiration:

https://jamesthom.as/2022/05/ai-powered-speed-camera/

Future ideas:

> The next step for this project would be to make it real-time. Rather than
> having to record videos and process them offline, the video stream should be
> processed and annotated live. This could be wrapped up into a mobile
> application to allow anyone with a mobile phone to use it. There are numerous
> TF models for real-time object detection which make this possible.

> It would also be interesting to take the same approach for running the
> software on a Raspberry PI with a web cam - to turn the “virtual speed
> camera” into a real hardware device.

Let's upgrade the thinking here.

I like the use of the AI/video service. This removes a lot of the processing on the device. 

If there is a connection, it could periodically upload and process data. If there is not, it could save on device.

Step one would be getting the loop running, record, send video to service for processing, dump annotations
Then add report saving
Then add parsing of data


... Capture video at certain times, so the script could run as a cron with a timer (for when to exit)
... This way we only capture certain windows of time, which will allow better use of credits.
... There's no need to capture all night, when no one is walking
... Focus on school hours (8-9am, 3-5pm).  3 hour window per day is 180 minutes, we get 1,000 free minutes per month.
    ... This will let us do almost a whole week (1,080 = 6 days). Can pay some pennies
