def calcula_score(
    preu,
    ma50,
    ma200,
    momentum,
    volatilitat,
    distancia_maxim,
    es_etf
):

    score = 0

    # Tendència curt termini
    if preu > ma50:
        score += 20

    # Tendència llarg termini
    if ma50 > ma200:
        score += 25

    # Momentum gradual
    if momentum > 0:
        score += min(momentum * 1.2, 30)

    # Força de tendència
    separacio = ((ma50 / ma200) - 1) * 100

    if separacio > 15:
        score += 15

    elif separacio > 10:
        score += 10

    elif separacio > 5:
        score += 5

    # Distància al màxim anual
    if distancia_maxim > -10:
        score += 15

    elif distancia_maxim > -20:
        score += 10

    # Volatilitat
    if volatilitat < 2:
        score += 10

    elif volatilitat < 3:
        score += 5

    # Bonus ETF
    if es_etf:
        score += 5

    # Bonus potencial

    if distancia_maxim < -20:
        score += 10

    elif distancia_maxim < -10:
        score += 5
        
    score = min(round(score), 100)

    return score