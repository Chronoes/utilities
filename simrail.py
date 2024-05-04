import time

def calc_time(distance_m, speed_kph):
    return distance_m / (speed_kph / 3.6)


def countdown(train_length):
    speed = int(input("Enter speed in km/h: "))
    t = int(round(calc_time(train_length, speed)+0.5))
    print(f"The time until speed limit changes is {t} seconds.")
    cycles = int(t/10)
    cycles = cycles if t % 10 >= 6 else cycles - 1
    for i in range(cycles):
        print(f"Time remaining: {t} seconds")
        time.sleep(10)
        t -= 10

    while t > 0:
        print(f"Time remaining: {t} seconds".ljust(40), end="\r")
        time.sleep(1)
        t -= 1

    print("\nTime's up!")

def main():
    train_length = 150
    # countdown(train_length)
    for speed in [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140]:
        t = int(round(calc_time(train_length, speed)+0.5))
        print(f"{speed} km/h - {t}s")

if __name__ == "__main__":
    main()
