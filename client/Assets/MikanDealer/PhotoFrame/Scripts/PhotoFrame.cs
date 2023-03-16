
using UdonSharp;
using UnityEngine;
using VRC.SDK3.Image;
using VRC.SDKBase;
using VRC.Udon;
using VRC.Udon.Common.Interfaces;

public class PhotoFrame : UdonSharpBehaviour
{
	public string Name;
	public bool AutoAdjust;
	[HideInInspector]
	public VRCUrl Url;

	const float FRAME_ADJUST = 0.1f;

	void Start()
	{
		var renderer = GetComponent<MeshRenderer>();
		if (renderer != null && !string.IsNullOrEmpty(Url.Get()) && renderer.material != null)
		{
			var downloader = new VRCImageDownloader();
			downloader.DownloadImage(Url, renderer.material, (IUdonEventReceiver)this);
		}
	}

	override public void OnImageLoadSuccess(IVRCImageDownload download)
	{
		if (AutoAdjust)
		{
			var tex = download.Result;
			float baseScale = 1;
			Vector3 scale;
			if (gameObject.transform.localScale.x > gameObject.transform.localScale.y) baseScale = gameObject.transform.localScale.x;
			if (gameObject.transform.localScale.x <= gameObject.transform.localScale.y) baseScale = gameObject.transform.localScale.y;

			if (tex.height > tex.width)
			{
				scale = new Vector3((float)tex.width / (float)tex.height, 1, 1);
			}
			else
			{
				scale = new Vector3(1, (float)tex.height / (float)tex.width, 1);
			}
			gameObject.transform.localScale = scale * baseScale;

			var renderer = GetComponent<MeshRenderer>();
			if (renderer != null)
			{
				renderer.sharedMaterial.SetFloat("ScaleX", 1 + scale.x * FRAME_ADJUST);
				renderer.sharedMaterial.SetFloat("ScaleY", 1 + scale.y * FRAME_ADJUST);
			}
		}
	}
}
