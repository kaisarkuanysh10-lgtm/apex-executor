export default function handler(req, res) {
    const ip = req.headers['x-forwarded-for'] || "Unknown";
    const ua = req.headers['user-agent'];

    // Логтарды толтыру
    console.log(`--- ATTACK DETECTED ---`);
    console.log(`IP: ${ip} | DEVICE: ${ua}`);

    // Әдейі 404 қайтару немесе ресурсты тауысу
    res.status(404).json({
        error: "Not Found",
        message: "This endpoint is under heavy load testing."
    });
}
