import datetime

import pendulum


class PendulumToolbox:
    @staticmethod
    def convert_timedelta_to_duration(
        timedelta: datetime.timedelta, in_words: bool = False
    ) -> pendulum.Duration | str:
        if timedelta is None:
            return "0 seconds"
        duration = pendulum.Duration(seconds=timedelta.total_seconds())
        if in_words:
            duration_in_words = duration.in_words(separator=",")
            return (
                duration_in_words
                if duration_in_words != "0 microseconds"
                else "0 seconds"
            )
        return duration
