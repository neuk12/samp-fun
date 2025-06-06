stock Float:MySqrt(Float:x)
{
    if (x <= 0.0) return 0.0;
    
    new Float:approx = x;
    new Float:better_approx;
    
    for (new i = 0; i < 10; i++)
    {
        better_approx = 0.5 * (approx + x / approx);
        approx = better_approx;
    }
    
    return approx;
}

stock Float:GetDistanceBetweenCoords3D(Float:x1, Float:y1, Float:z1, Float:x2, Float:y2, Float:z2)
{
    new Float:dx = x2 - x1;
    new Float:dy = y2 - y1;
    new Float:dz = z2 - z1;

    return MySqrt(dx*dx + dy*dy + dz*dz);
}



stock IsPlayerInRangeOfPlayer(playerid, targetid, Float:range)
{
    new Float:x1, Float:y1, Float:z1;
    new Float:x2, Float:y2, Float:z2;

    if (!IsPlayerConnected(playerid) || !IsPlayerConnected(targetid))
        return 0;

    GetPlayerPos(playerid, x1, y1, z1);
    GetPlayerPos(targetid, x2, y2, z2);

    new Float:dist = GetDistanceBetweenCoords3D(x1, y1, z1, x2, y2, z2);

    return (dist <= range) ? 1 : 0;
}
