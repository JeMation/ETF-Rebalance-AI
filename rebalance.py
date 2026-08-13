def calculate_rebalance(current, target, total_amount=10000000):

    result = {}

    for ticker in target:

        current_weight = current.get(ticker, 0)
        target_weight = target[ticker]

        diff = round(target_weight - current_weight, 2)


        amount = round(
            total_amount * diff / 100,
            0
        )


        if diff > 0:
            action = "BUY"

        elif diff < 0:
            action = "SELL"

        else:
            action = "HOLD"


        result[ticker] = {

            "current": current_weight,

            "target": target_weight,

            "difference": diff,

            "amount": amount,

            "action": action

        }


    return result