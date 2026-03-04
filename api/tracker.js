export default function handler(req, res) {
    // 1. Пайдаланушының IP-ін анықтау
    // Vercel-де нақты IP 'x-forwarded-for' тақырыбында болады
    const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;

    // 2. Құрылғы туралы ақпаратты алу (iPhone 14, 11, Windows т.б.)
    const userAgent = req.headers['user-agent'] || 'Unknown Device';

    // 3. Қай беттен келгенін анықтау
    const referer = req.headers['referer'] || 'Direct Access';

    // 4. Уақытты белгілеу
    const timestamp = new Date().toISOString();

    // VERCEL LOGS-қа шығару (Сен мұны терминалдан көресің)
    console.log("-----------------------------------------");
    console.log(`[${timestamp}] ЖАҢА КІРУ ТІРКЕЛДІ!`);
    console.log(`IP Мекенжайы: ${ip}`);
    console.log(`Құрылғы (UA): ${userAgent}`);
    console.log(`Келген жері: ${referer}`);
    console.log("-----------------------------------------");

    // Скриптке жауап қайтару (Статус 200 OK)
    res.status(200).json({
        success: true,
        message: "Data tracked successfully",
        your_ip: ip,
        your_device: userAgent
    });
}
