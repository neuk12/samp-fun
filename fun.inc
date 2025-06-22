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


/**
 * @brief Formatea un número entero agregando un delimitador cada 3 cifras.
 *
 * @param integer          El número entero a formatear.
 * @param delimiter[]      (Opcional) El string a usar como delimitador. Por defecto es ",".
 *
 * @returns string         Devuelve un string con el número formateado.
 *
 * @note Si el número es negativo, el signo se mantiene al principio y no se le insertan separadores antes de él.
 *
 * @example
 *    new str[24];
 *    str = IntegerWithDelimiter(1234567);               // str = "1,234,567"
 */
IntegerWithDelimiter(integer, const delimiter[] = ",") {
    new string[16];

    format(string, sizeof string, "%i", integer);

    for (new i = strlen(string) - 3, j = ((integer < 0) ? 1 : 0); i > j; i -= 3) {

        strins(string, delimiter, i, sizeof string);
    }

    return string;
}

stock IsPlayerInRange2D(playerid, targetid, Float:range)
{
    new Float:x1, y1, z1;
    new Float:x2, y2, z2;

    if (!IsPlayerConnected(playerid) || !IsPlayerConnected(targetid))
        return 0;

    GetPlayerPos(playerid, x1, y1, z1);
    GetPlayerPos(targetid, x2, y2, z2);

    new Float:dx = x2 - x1;
    new Float:dy = y2 - y1;

    return (floatsqrt(dx*dx + dy*dy) <= range) ? 1 : 0;
}


stock GenerateInviteCode(dest[], size)
{
    new const charset[] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    new len = strlen(charset);

    for (new i = 0; i < size - 1; i++)
    {
        dest[i] = charset[random(len)];
    }
    dest[size - 1] = '\0';
}



/**
 * Reemplaza en el string todas las secuencias '\n' por el carácter de salto de línea real (0x0A).
 * 
 * @param string[] Cadena en la que se buscarán y reemplazarán las secuencias '\n'.
 */
stock ReplaceEscapedNewlines(string[])
{
    new len = strlen(string);  // Obtenemos la longitud actual de la cadena

    // Recorremos la cadena hasta el penúltimo carácter
    for (new i = 0; i < len - 1; i++)
    {
        // Verificamos si en la posición actual y la siguiente hay la secuencia '\' y 'n'
        if (string[i] == '\\' && string[i+1] == 'n')
        {
            string[i] = 0x0A; // Reemplazamos '\' por el salto de línea real (ASCII 10)

            // Desplazamos todos los caracteres posteriores un lugar hacia la izquierda
            // para eliminar el carácter 'n' que queda tras reemplazar '\'
            for (new j = i+1; j < len; j++)
            {
                string[j] = string[j+1];
            }

            len--; // Actualizamos la longitud ya que hemos eliminado un carácter
            // Nota: No incrementamos i para no saltar el siguiente carácter tras el desplazamiento
        }
    }
}

