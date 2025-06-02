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
