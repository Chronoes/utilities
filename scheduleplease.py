import argparse
import datetime
import requests
import sys

days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_numeric_day(day):
    day = day.lower()[:3]
    return days.index(day.lower())


# tz_string = datetime.datetime.now().astimezone().tzname()
schedule_url = "https://subsplease.org/api/?f=schedule&tz=Etc/GMT"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get schedule from SubsPlease and match them to simulwatch sessions")
    parser.add_argument(
        "--filter", "-f", help="File of a list of shows to filter results. Must be exact match, one per line."
    )
    parser.add_argument("--show-time", "-t", help="Show scheduled time for each show in the list.",
                        nargs="?", choices=["all", "release"], const="all", default=None)
    parser.add_argument(
        "--sort", "-s", help="Sort shows by given metric.", choices=["default", "title", "datetime"], default="default"
    )
    parser.add_argument(
        "daytime",
        nargs="+",
        help='Day and time of simulwatch sessions in format "day-hh[:mm]" (e.g. "mon-20:00", "mon-20") or just "day" (e.g. "mon") which defaults the time to 23:59. All times are UTC',
    )
    args = parser.parse_args()
    if len(args.daytime) < 2:
        parser.print_usage()
        print("At least two daytime arguments are needed to create schedule")
        sys.exit(1)

    if args.filter:
        with open(args.filter) as f:
            filter_shows = f.read().splitlines()
    else:
        filter_shows = []

    datetimes = []
    for dt in args.daytime:
        parts = dt.split("-")
        if len(parts) == 1:
            parts = [parts[0], "23:59"]
        elif ":" not in parts[1]:
            parts[1] += ":00"
        day, time = parts
        datetimes.append((get_numeric_day(day), time, []))

    datetimes = sorted(datetimes, key=lambda dt: dt[0])
    frst = datetimes[0]
    # Add next week's first day to the list for ease of comparison later
    datetimes.append((frst[0] + 7, frst[1], frst[2]))

    # The comparison will be made with the timestring in the format "weekday-hh:mm". Numeric weekday is zero-padded for comparison
    datetimes = [(f"{day:02}-{time}", shows) for day, time, shows in datetimes]

    schedule = requests.get(schedule_url).json()["schedule"]

    for day_name, series in schedule.items():
        for show in series:
            if filter_shows and show["title"] not in filter_shows:
                continue
            schedule_day = get_numeric_day(day_name)
            # Because schedules will wrap around to next week, we test both this week and next week
            # This is also why we have the next week's first day placeholder in datetimes list
            primary_sort_key = f'{schedule_day:02}-{show["time"]}'
            schedule_days = [primary_sort_key, f'{schedule_day+7:02}-{show["time"]}']
            # print(show['title'])
            for i, curr_day in enumerate(datetimes[1:], 1):
                prev_day = datetimes[i - 1]
                # print(prev_day[0], schedule_days, curr_day[0])
                if any(prev_day[0] < schedule_day and schedule_day <= curr_day[0] for schedule_day in schedule_days):
                    show["day"] = day_name
                    show["sort_datetime"] = primary_sort_key
                    curr_day[1].append(show)
                    break

    # Remove the placeholder for next week's first day. The show list shares the same reference so no other operation is needed
    datetimes.pop()

    for dt, shows in datetimes:
        reverse = False
        sort_fn = None
        if args.sort == "title":
            sort_fn = lambda show: show["title"]
        elif args.sort == "datetime":
            sort_fn = lambda show: ("0" if show["sort_datetime"] > dt else "1") + show["sort_datetime"]
        elif filter_shows:
            sort_fn = lambda show: filter_shows.index(show["title"])
            reverse = True

        day_num, time = dt.split("-")
        day_name = days_full[int(day_num)]
        print(f"@ {day_name} {time} UTC")
        i = 1
        sorted_shows = sorted(shows, key=sort_fn, reverse=reverse) if sort_fn else shows
        for show in sorted_shows:
            if args.show_time == "release" and show["day"] == day_name:
                print(f'{i}. {show["title"]} (@ {show["time"]})')
            elif args.show_time == "all":
                print(f'{i}. {show["title"]} ({show["day"]} {show["time"]})')
            else:
                print(f'{i}. {show["title"]}')
            i += 1
        print()
