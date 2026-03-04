export default function handler(req, res) {
    // Хакер Proxy қолданса да, шын IP-ді іздеу
    const forwarded = req.headers["x-forwarded-for"];
    const real_ip = forwarded ? forwarded.split(',')[0] : req.socket.remoteAddress;

    const user_agent = req.headers["user-agent"];

    console.log("--- ЖАҢА КЕЛУШІ ---");
    console.log(`IP: ${real_ip}`);
    console.log(`Құрылғы: ${user_agent}`);

    res.status(200).json({
        message: "Анықталды",
        your_ip: real_ip,
        device: user_agent
    });
}
